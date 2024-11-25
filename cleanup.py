import subprocess

def clean_requirements(input_file, output_file):
    try:
        # Read the original requirements.txt file
        with open(input_file, 'r') as file:
            lines = file.readlines()

        # Set up a list to hold cleaned packages
        cleaned_requirements = []

        for line in lines:
            # Ignore empty lines and comments
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # Check if package is from a file path (we'll ignore those)
            if "@" in line:
                continue
            
            # Extract package name and version
            if '==' in line:
                package, version = line.split('==')
                # Use pip to check installed version
                result = subprocess.run(
                    ['pip', 'show', package], stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                
                if result.returncode == 0:
                    # Extract installed version
                    installed_version = result.stdout.decode().split('Version: ')[1].split('\n')[0]
                    cleaned_requirements.append(f"{package}=={installed_version}")
                else:
                    # If package is not found, just keep the original
                    cleaned_requirements.append(line)
            else:
                # If no version is specified, keep the package as is
                cleaned_requirements.append(line)

        # Write the cleaned requirements to the output file
        with open(output_file, 'w') as file:
            for req in cleaned_requirements:
                file.write(req + '\n')

        print(f"Cleaned requirements saved to {output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Usage example:
clean_requirements('requirements.txt', 'cleaned_requirements.txt')
