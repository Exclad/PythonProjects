import torch

# This is the most important check.
is_available = torch.cuda.is_available()

print(f"Is CUDA available? -> {is_available}")

if is_available:
    # Get the number of GPUs available
    device_count = torch.cuda.device_count()
    print(f"Number of GPUs found: {device_count}")

    # Get the name of the current GPU
    current_device_name = torch.cuda.get_device_name(0)
    print(f"Current GPU Name: {current_device_name}")

    # Get the CUDA version PyTorch was compiled with
    pytorch_cuda_version = torch.version.cuda
    print(f"PyTorch was compiled with CUDA version: {pytorch_cuda_version}")
else:
    print("\nPyTorch cannot find a CUDA-enabled GPU.")
    print("This is likely because you installed the CPU-only version of PyTorch.")
    print("Please follow the re-installation steps.")