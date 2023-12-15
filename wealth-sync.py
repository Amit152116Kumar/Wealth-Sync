import os
import subprocess


def run_command(command):
    """Run a shell command and return its output"""
    print("Run command: ", command)
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        text=True,
        bufsize=1,
    )
    output = ""
    for line in iter(process.stdout.readline, ""):
        print(line, end="")
        output += line

    process.stdout.close()
    returncode = process.wait()
    if returncode != 0:
        print("Return code: ", returncode)
    return output, returncode


def create_cronjob(cwd, env_path):
    """Add crontab to run the livefeed at 8:00 AM and 9:14 AM and 3:31 PM for the weekdays"""
    # Add crontab only if it doesn't exist
    output, returncode = run_command(f"crontab -l | grep localhost:8080")
    if output:
        print("Crontab already exists")
        return
    # Replace env path in restart.sh
    with open("restart.sh", "r") as f:
        content = f.read()
        content = content.replace("ENV_PATH", env_path)

        # Write the content to the restart.sh file
        with open("service_restart.sh", "w") as f:
            f.write(content)
        
    run_command("chmod +x service_restart.sh")
    run_command(
        f"crontab -l | {{ cat; echo '0 7 * * * {cwd}/service_restart.sh'; }} | crontab -"
    )

    run_command(
        f"crontab -l | {{ cat; echo '0 8 * * 1-5 curl -X GET http://localhost:8080/fetchTokens'; }} | crontab -"
    )

    run_command(
        f"crontab -l | {{ cat; echo '14 9 * * 1-5 curl -X GET http://localhost:8080/subscribe'; }} | crontab -"
    )

    run_command(
        f"crontab -l | {{ cat; echo '31 15 * * 1-5 curl -X GET http://localhost:8080/unsubcribe'; }} | crontab -"
    )

    return


def delete_cronjob():
    """Delete crontab to run the livefeed at 8:00 AM and 9:14 AM and 3:31 PM for the weekdays"""
    run_command(f"crontab -l | sed '/restart/d' | crontab -")
    run_command(f"crontab -l | sed '/localhost:8080/d' | crontab -")
    return


def create_conda_env():
    # check if conda is installed
    run_command("conda --version")
    output, _ = run_command("conda env list | grep wealth-sync")
    
    if output:
        print("Conda environment already exists")
    else:
        # Create a conda environment with the name wealth-sync
        run_command("conda create -n wealth-sync python=3.10 -y")
        output, _ = run_command("conda env list | grep wealth-sync")
    
    env_path = output.split(" ")[-1].strip()

    # Install the required packages
    run_command(f"{env_path}/bin/pip install -r requirements.txt")
    return env_path


def delete_conda_env():
    # check if conda is installed
    run_command("conda --version")

    # Delete the conda environment with the name wealth-sync
    run_command("conda env remove -n wealth-sync")
    return


def enable_wealth_sync_service(user, cwd, env_path):
    # Open the wealth-sync.service file and replace the current working directory and user
    with open("wealth-sync.service", "r") as f:
        content = f.read()
        content = content.replace("CWD", cwd)
        content = content.replace("USER", user)
        content = content.replace("ENV_PATH", env_path)

        # Write the content to the /etc/systemd/system/wealth-sync.service file with sudo
        with open("wealth-sync.service", "w") as f:
            f.write(content)

    run_command("sudo cp wealth-sync.service /etc/systemd/system/")
    print("File written to /etc/systemd/system/wealth-sync.service")

    # Enable the wealth-sync.service
    run_command("sudo systemctl enable wealth-sync.service")

    # Start the wealth-sync.service
    run_command("sudo systemctl start wealth-sync.service")

    # Check the status of the wealth-sync.service
    run_command("systemctl status wealth-sync.service")


def disable_wealth_sync_service():
    # Stop the wealth-sync.service file
    run_command("sudo systemctl stop wealth-sync.service")

    # Disable the wealth-sync.service file
    run_command("sudo systemctl disable wealth-sync.service")

    # Delete the wealth-sync.service file
    run_command("sudo rm /etc/systemd/system/wealth-sync.service")


# Get the current working directory
cwd = os.getcwd()
# Get the User of linux system
user = run_command("echo $USER")[0].strip()

print("Current working directory: ", cwd)

response = input("Do you want to install wealth-sync? (y/n): ")
if response == "y":
    # Create a conda environment with the name wealth-sync
    env_path = create_conda_env()

    # Add crontab to run the livefeed at 8:00 AM and 9:14 AM and 3:31 PM for the weekdays
    create_cronjob(cwd, env_path)

    # Create a logs directory
    run_command("mkdir logs")

    # Enable the wealth-sync.service
    enable_wealth_sync_service(user, cwd, env_path)

    print("wealth-sync installed successfully")

    print("Please restart the system to start the wealth-sync service")

elif response == "n":
    response = input("Do you want to uninstall wealth-sync? (y/n): ")
    if response == "y":
        # Delete the conda environment with the name wealth-sync
        delete_conda_env()

        # Delete crontab to run the livefeed at 8:00 AM and 9:14 AM and 3:31 PM for the weekdays
        delete_cronjob()

        # Disable the wealth-sync.service
        disable_wealth_sync_service()

        print("wealth-sync uninstalled successfully")
    else:
        print("Please enter a valid response")
