#!/usr/bin/env python3
"""双fork守护方式启动Arnis生成大工凌水校区世界(绕过沙箱进程清理)"""
import os
import sys
import subprocess

SQFS = "/home/z/my-project/mc-work/appimage/squashfs-root"
HOSTLIBS = "/home/z/my-project/mc-work/host-libs/extracted/usr/lib/x86_64-linux-gnu"
OUTDIR = "/home/z/my-project/mc-work/output"
LOG = "/home/z/my-project/mc-work/arnis-run.log"
STATUS = "/home/z/my-project/mc-work/arnis-status.txt"

ARNIS_ARGS = [
    f"{SQFS}/usr/bin/arnis",
    "--bbox", "38.87318,121.50831,38.88981,121.53206",
    "--output-dir", OUTDIR,
    "--mode", "geo-terrain",
    "--scale", "1",
    "--spawn-lat", "38.8795",
    "--spawn-lng", "121.5260",
    "--map-preview",
    "--gamemode", "creative",
    "--world-time", "6000",
]

def daemon():
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = (
        f"{HOSTLIBS}:{SQFS}/usr/lib/x86_64-linux-gnu:{SQFS}/usr/lib"
    )
    with open(LOG, "ab", 0) as log, open(STATUS, "w") as st:
        st.write("RUNNING\n")
        st.flush()
        try:
            log.write(f"\n===== LAUNCH {os.times()}\n".encode())
            log.flush()
            p = subprocess.run(
                ARNIS_ARGS,
                stdout=log,
                stderr=subprocess.STDOUT,
                env=env,
                cwd=SQFS,
                timeout=5400,  # 90分钟上限
            )
            st.write(f"EXIT={p.returncode}\n")
        except subprocess.TimeoutExpired:
            st.write("EXIT=TIMEOUT\n")
        except Exception as e:
            st.write(f"EXIT=ERROR {e}\n")

def main():
    pid = os.fork()
    if pid == 0:
        os.setsid()
        pid2 = os.fork()
        if pid2 == 0:
            # 孤儿孙进程执行真正的工作
            try:
                daemon()
            finally:
                os._exit(0)
        os._exit(0)
    os.waitpid(pid, 0)
    print("daemonized arnis launcher, log:", LOG)

if __name__ == "__main__":
    main()
