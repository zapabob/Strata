call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
set "PATH=C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja;%PATH%"
set "CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3"
set "CUDA_PATH_V13_3=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3"
cmake -G Ninja -S "H:\Strata\worktrees\hakua-chatbot-20261027" -B "H:\Strata\worktrees\hakua-chatbot-20261027\build-cuda-sm120-verify" -DCMAKE_BUILD_TYPE=Release -DSTRATA_ENABLE_CUDA=ON -DSTRATA_BUILD_TESTS=OFF -DSTRATA_PORTABLE=ON "-DCMAKE_CUDA_ARCHITECTURES=120" "-DCMAKE_CUDA_COMPILER=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3/bin/nvcc.exe" "-DCUDAToolkit_ROOT=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3" "-DSTRATA_GGML_DIR=H:\Strata\deps\ggml-3cf03257"
echo CONFIG_EXIT=%ERRORLEVEL%
