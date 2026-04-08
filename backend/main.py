from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import meep as mp
import numpy as np
import base64
import traceback

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.post("/simulate_animation")
async def simulate_animation(data: dict):
    try:
        # 获取前端参数
        sx, sy, sz = data['size_x'], data['size_y'], data['size_z']
        res, bg_eps = data['res'], data['bg_eps']
        
        cell = mp.Vector3(sx, sy, sz)
        geometry = [
            mp.Sphere(radius=1.0, material=mp.Medium(epsilon=1.5), center=mp.Vector3(-sx/4, 0, 0)),
            mp.Block(size=mp.Vector3(2,2,2), material=mp.Medium(epsilon=2.5), center=mp.Vector3(sx/10, 0, 0)),
            mp.Cone(radius=1.0, height=2.0, material=mp.Medium(epsilon=3.5), center=mp.Vector3(0, sy/4, 0))
        ]
        
        sources = [mp.Source(mp.GaussianSource(1.0, fwidth=0.2), component=mp.Ez, center=mp.Vector3(0, 0, 0))]
        
        sim = mp.Simulation(
            cell_size=cell,
            boundary_layers=[mp.PML(1.0)],
            geometry=geometry,
            sources=sources,
            default_material=mp.Medium(epsilon=bg_eps),
            resolution=res
        )

        frames = []
        def capture_frame(s):
            # 获取 Ez 场并进行下采样
            d = s.get_array(center=mp.Vector3(), size=cell, component=mp.Ez)
            frames.append(d[::2, ::2, ::2].astype(np.float32))

        # 运行仿真
        sim.run(mp.at_every(5, capture_frame), until=50) # 增大间隔减少数据量
        
        video_data = np.array(frames)
        encoded_data = base64.b64encode(video_data.tobytes()).decode('utf-8')
        
        return {
            "status": "success",
            "shape": video_data.shape,
            "data": encoded_data
        }
    except Exception as e:
        # 如果报错，把具体的错误堆栈发给前端，方便调试
        error_msg = traceback.format_exc()
        print(error_msg)
        return {"status": "error", "message": str(e), "trace": error_msg}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)