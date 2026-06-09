# services/hpc.py
import subprocess
import json
import os
from typing import Optional

class HPCService:
    @staticmethod
    def submit_job(job_id: int, config_data: dict) -> bool:
        """
        动作：派发仿真任务
        职责：把参数保存成文件，并异步启动计算端脚本。
        """
        # 1. 动态生成独立的参数配置文件名称
        # 例如: config_1.json, config_2.json
        # 这样多用户同时点击计算时，各自的文件完全隔离，绝对不会发生数据覆盖。
        config_filename = f"config_{job_id}.json"
        
        # 2. 将前端传过来的 Meep 参数字典写入本地的临时 JSON 文件中
        with open(config_filename, "w") as f:
            json.dump(config_data, f)
            
        try:
            # 3. 【核心技巧】使用 subprocess.Popen 异步拉起计算脚本
            # script_path 指向真正的仿真脚本 hpc_scripts/run_simulation.py
            script_path = os.path.join("hpc_scripts", "run_simulation.py")
            
            # Popen 是非阻塞的！它相当于在系统后台新开了一个黑窗口（终端）去跑计算，
            # 扔下命令后，FastAPI 主线程会立刻继续往下走，从而保证网页不会卡死。
            # 我们把 job_id 和配置路径作为命令行参数传给它：python run_simulation.py 1 config_1.json
            subprocess.Popen(["python", script_path, str(job_id), config_filename])
            
            # 顺利拉起，向 main.py 汇报成功
            return True
        except Exception as e:
            print(f"Error submitting job: {e}")
            return False

    @staticmethod
    def check_result(job_id: int) -> Optional[dict]:
        """
        动作：检查并获取计算结果
        职责：看看仿真脚本是不是把结果文件吐出来了。
        """
        # 1. 根据约定的命名规则，定位该任务应该产生的结果文件
        # 例如: result_1.json
        result_filename = f"result_{job_id}.json"
        
        # 2. 检查这个文件在磁盘上是否存在
        if os.path.exists(result_filename):
            # 3. 如果存在，说明后台的 Meep 已经算完了！
            # 我们把结果 JSON 读取出来，解析成 Python 字典返回
            with open(result_filename, "r") as f:
                data = json.load(f)
            return data
            
        # 4. 如果文件还没出来，说明 Meep 还在努力计算中，返回 None
        return None