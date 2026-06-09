# hpc_scripts/run_simulation.py
import sys
import json
import time

def main():
    # 1. 安全检查：确保 FastAPI 传过来了必需的两个参数
    # sys.argv[0] 是脚本名字本身
    # sys.argv[1] 是自增的 job_id
    # sys.argv[2] 是配置文件的路径 config_JOBID.json
    if len(sys.argv) < 3:
        print("[HPC Error] Missing arguments.")
        return
    
    job_id = sys.argv[1]
    config_path = sys.argv[2]
    
    # 2. 读取从 FastAPI 服务端传过来的物理参数
    with open(config_path, "r") as f:
        config = json.load(f)
        
    print(f"[HPC Worker] Job {job_id} started. Parsing parameters...")
    
    # =============================================================
    # 3. 【核心修改点】模拟长时 FDTD 仿真
    # MVP 阶段我们用 time.sleep(5) 假装它努力算了几秒钟。
    # 
    # 💡 以后真正的 Meep 代码就是直接写在这里：
    #    import meep as mp
    #    fcen = config.get("fcen")
    #    ...
    #    sim = mp.Simulation(...)
    #    sim.run(..., until=...)
    # =============================================================
    # time.sleep(3)
    
    # 4. 模拟生成仿真计算的数据结果
    # 我们从配置中拿出中心频率 fcen，并随便生成一些通量数据（Flux）
    fcen = config.get("fcen", 1.0)
    mock_result = {
        "frequencies": [fcen - 0.1, fcen, fcen + 0.1],
        "flux": [0.25, 0.98, 0.12]
    }
    
    # 5. 【关键协同点】将计算结果写回约定的文件名中
    # 文件名必须长成 result_JOBID.json，这样 FastAPI 的 HPCService 才能精准捞到它
    result_filename = f"result_{job_id}" + ".json"
    with open(result_filename, "w") as f:
        json.dump(mock_result, f)
        
    print(f"[HPC Worker] Job {job_id} completed. Result file generated.")

if __name__ == "__main__":
    main()