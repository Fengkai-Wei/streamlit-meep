# main.py
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
import json

# 导入我们之前已经讲过的三个模块
from database import engine, Base, get_db
import models
import schemas
# 导入业务逻辑层：负责和计算端打交道的服务
from services.hpc import HPCService

# ==========================================
# 1. 自动初始化数据库表
# ==========================================
# 这行代码会让 SQLAlchemy 检查本地数据库。
# 如果发现没有 simulation_jobs 表，就会根据 models.py 的定义自动创建它。
Base.metadata.create_all(bind=engine)

# ==========================================
# 2. 实例化 FastAPI 应用
# ==========================================
app = FastAPI(title="Meep Decoupled Backend")


# ==========================================
# 3. 路由 1：极简用户登录验证
# ==========================================
@app.post("/api/login")
def login(user: schemas.UserLogin):
    """
    接收 Pydantic 验证过的登录数据。
    目前是 MVP 阶段，我们直接硬编码一个账号用于本地联调。
    """
    if user.username == "Fengkai" and user.password == "123456":
        return {"status": "SUCCESS", "token": "mock-token-fengkai", "user_id": "Fengkai"}
    
    # 如果账号密码不对，抛出 HTTP 400 异常错误
    raise HTTPException(status_code=400, detail="Invalid credentials")


# ==========================================
# 4. 路由 2：接收 Meep 参数并提交计算
# ==========================================
# Depends(get_db): 核心魔术！在收到请求时自动创建数据库 session，并注入到 db 变量中
@app.post("/api/simulation/submit")
def submit_simulation(payload: schemas.JobSubmit, db: Session = Depends(get_db)):
    """
    当前端 Streamlit 点击“开始计算”时，参数会打到这个接口。
    """
    # 步骤 A：把前端安全的参数格式化，准备写入数据库
    db_job = models.DBJob(
        user_id=payload.user_id,
        project_name=payload.project_name,
        status="SAVED",
        # 划重点：这里利用 json.dumps 把 Pydantic 字典压缩成了大文本字符串存入数据库
        config_json=json.dumps(payload.config)
    )
    
    # 步骤 B：执行数据库持久化命令
    db.add(db_job)      # 将任务放入暂存区
    db.commit()     # 真正提交到 SQLite 文件，此时 db_job.id 自动生成（比如变成 1）
    db.refresh(db_job)  # 刷新对象，确保我们在 Python 里能拿到最新的自增 ID

    # 步骤 C：调用解耦的业务层，把任务丢给计算端（本地模拟脚本/集群）
    # 我们把刚刚生成的独一无二的自增 ID 和配置传过去
    success = HPCService.submit_job(db_job.id, payload.config)
    
    # 步骤 D：根据服务层返回的启动状态，更新数据库
    if success:
        db_job.status = "RUNNING"  # 派发成功，状态变为运行中
        db.commit()                # 更新数据库状态
        return {"status": "SUCCESS", "job_id": db_job.id}
    else:
        db_job.status = "FAILED"   # 派发失败
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to dispatch job to compute node")


# ==========================================
# 5. 路由 3：供前端实时查询/轮询状态的接口
# ==========================================
@app.get("/api/simulation/status/{job_id}")
def get_simulation_status(job_id: int, db: Session = Depends(get_db)):
    """
    前端 Streamlit 会用 while 循环或者定时器，每隔几秒请求一次这个接口。
    """
    # 步骤 A：去数据库查一下有没有这个任务
    db_job = db.query(models.DBJob).filter(models.DBJob.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 步骤 B：如果数据库记录该任务“正在运行”，我们就去计算侧看看结果出来了没有
    if db_job.status == "RUNNING":
        # 调用服务层检查本地有没有生成对应的结果文件
        result_data = HPCService.check_result(job_id)
        
        if result_data is not None:
            # 如果结果文件出来了，说明算完了！立刻把数据库状态改为已完成
            db_job.status = "COMPLETED"
            db.commit()
            # 把最新的状态和计算出的光学谱线数据打包返回给前端
            return {"job_id": job_id, "status": "COMPLETED", "result_data": result_data}
            
    # 步骤 C：如果数据库记录原本就已经完成了（COMPLETED），再次查询时直接去抓结果返回
    if db_job.status == "COMPLETED":
        result_data = HPCService.check_result(job_id)
        return {"job_id": job_id, "status": "COMPLETED", "result_data": result_data}

    # 步骤 D：如果还在算，或者排队中，直接返回当前状态，result_data 为 None
    return {"job_id": job_id, "status": db_job.status, "result_data": None}