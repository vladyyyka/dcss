#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
import threading
import time
from datetime import datetime

import requests
from pymavlink import mavutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.evaluator.factory import get_quest_checker


def log_to_file(guid, message):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{guid}.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} - {message}\n")


def send_progress(guid, manager_url, internal_token, data):
    try:
        requests.post(
            f"{manager_url}/quest/{guid}/progress",
            json=data,
            headers={"X-Internal-Token": internal_token},
            timeout=2,
        )
    except Exception as e:
        print(f"Не удалось отправить прогресс: {e}")


def forward(src, dst):
    while True:
        try:
            msg = src.recv_match(blocking=True)
            if msg:
                dst.mav.send(msg)
        except Exception:
            break


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--guid", required=True)
    parser.add_argument("--type_id", type=int, required=True)
    parser.add_argument("--sitl_port", type=int, required=True)
    parser.add_argument("--proxy_port", type=int, required=True)
    parser.add_argument("--manager_url", default="http://127.0.0.1:8000")
    parser.add_argument("--internal_token", required=True)
    parser.add_argument("--sim_vehicle_path", required=True)
    parser.add_argument("--vehicle", default="ArduCopter")
    parser.add_argument("--startup_delay", type=int, default=15)
    parser.add_argument("--instance", type=int, default=0)
    args, extra_args = parser.parse_known_args()

    guid = args.guid
    sitl_proc = None

    try:
        log_to_file(guid, f"Запущен evaluator для задания {guid}, тип {args.type_id}")

        if not os.path.exists(args.sim_vehicle_path):
            raise FileNotFoundError(f"sim_vehicle.py не найден: {args.sim_vehicle_path}")

        sitl_cmd = [
            args.sim_vehicle_path,
            "-v", args.vehicle,
            "-I", str(args.instance),
            "--map",
            "--console",
            "--out", f"127.0.0.1:{args.sitl_port}",
        ] + extra_args

        log_to_file(guid, "Запуск SITL: " + " ".join(sitl_cmd))
        sitl_proc = subprocess.Popen(sitl_cmd)
        log_to_file(guid, "SITL запущен, ожидание инициализации...")
        time.sleep(args.startup_delay)

        log_to_file(guid, f"Подключение к MAVLink UDP 127.0.0.1:{args.sitl_port}...")
        master_in = mavutil.mavlink_connection(f"udp:127.0.0.1:{args.sitl_port}")
        master_in.wait_heartbeat()
        log_to_file(guid, "Heartbeat получен, соединение с SITL установлено.")

        log_to_file(guid, f"Открытие TCP-сервера для Mission Planner на порту {args.proxy_port}...")
        master_out = mavutil.mavlink_connection(f"tcpin:0.0.0.0:{args.proxy_port}", input=False)
        log_to_file(guid, f"Ожидание подключения Mission Planner на порту {args.proxy_port}")
        time.sleep(0.5)

        threading.Thread(target=forward, args=(master_in, master_out), daemon=True).start()
        threading.Thread(target=forward, args=(master_out, master_in), daemon=True).start()

        checker = get_quest_checker(args.type_id)
        checker.guid = guid

        last_progress_time = 0
        progress_interval = 2

        while True:
            msg = master_in.recv_match(blocking=True)
            if not msg:
                continue

            msg_type = msg.get_type()
            checker.update(msg_type, msg)

            now = time.time()
            if now - last_progress_time >= progress_interval:
                progress = checker.get_progress()
                checklist = [{"check_id": k, "progress": v} for k, v in progress.items()]
                elapsed = getattr(checker, "state", {}).get("flight_time", 0)
                data = {"checklist": checklist, "elapsed_time_sec": elapsed}
                send_progress(guid, args.manager_url, args.internal_token, data)
                log_to_file(guid, f"Прогресс: {progress}")
                last_progress_time = now

            if checker.is_finished():
                success = checker.get_final_result()
                final_data = {
                    "status": "completed",
                    "result": "success" if success else "fail",
                    "completed_at": datetime.utcnow().isoformat(),
                }
                send_progress(guid, args.manager_url, args.internal_token, final_data)
                log_to_file(guid, f"Задание завершено. Успех: {success}")
                break

    except Exception as exc:
        log_to_file(guid, f"Ошибка evaluator: {exc}")
        send_progress(
            guid,
            args.manager_url,
            args.internal_token,
            {
                "status": "aborted",
                "result": "fail",
                "completed_at": datetime.utcnow().isoformat(),
            },
        )
        raise
    finally:
        if sitl_proc and sitl_proc.poll() is None:
            sitl_proc.terminate()
            try:
                sitl_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                sitl_proc.kill()
        log_to_file(guid, "Evaluator завершён")


if __name__ == "__main__":
    main()
