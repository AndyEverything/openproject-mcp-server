# install_mcp.ps1
# Script cài đặt tự động OpenProject MCP cho Claude Desktop
# Hướng dẫn: Click chuột phải -> Run with PowerShell

$ErrorActionPreference = "Stop"

Write-Host ">>> Đang bắt đầu cài đặt OpenProject MCP..." -ForegroundColor Cyan

# 1. Xác định đường dẫn project
$ScriptPath = $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path (Split-Path $ScriptPath -Parent) -Parent
Write-Host "📂 Thư mục dự án: $ProjectRoot"

# 2. Kiểm tra Python Virtual Environment (.venv)
$VenvPython = "$ProjectRoot\.venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "❌ Không tìm thấy môi trường ảo (.venv). Đang thử tạo mới..." -ForegroundColor Yellow
    # Kiểm tra xem có 'uv' không
    if (Get-Command "uv" -ErrorAction SilentlyContinue) {
        Write-Host "Running 'uv sync'..."
        Set-Location $ProjectRoot
        uv sync
    } else {
        Write-Error "Vui lòng cài đặt 'uv' hoặc chạy setup thủ công trước khi chạy script này."
        Pause
        Exit
    }
}

if (-not (Test-Path $VenvPython)) {
    Write-Error "Vẫn không tìm thấy python trong .venv. Cài đặt thất bại."
    Pause
    Exit
}

# 3. Thu thập thông tin từ người dùng
Write-Host "`n🔐 Cấu hình kết nối OpenProject" -ForegroundColor Cyan
$OpenProjectUrl = Read-Host "Nhập URL OpenProject (ví dụ: https://company.openproject.com)"
if ([string]::IsNullOrWhiteSpace($OpenProjectUrl)) {
    Write-Error "URL không được để trống."
    Exit
}

$ApiKey = Read-Host "Nhập API Key của bạn (Lấy trong My Account > Access Tokens)"
if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    Write-Error "API Key không được để trống."
    Exit
}

# 4. Cập nhật Config Claude Desktop
$ConfigFile = "$env:APPDATA\Claude\claude_desktop_config.json"
$ConfigDir = Split-Path $ConfigFile -Parent

if (-not (Test-Path $ConfigDir)) {
    New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
}

$ConfigJson = @{}
if (Test-Path $ConfigFile) {
    try {
        $Content = Get-Content $ConfigFile -Raw -Encoding UTF8
        $ConfigJson = $Content | ConvertFrom-Json -Depth 10 # Depth để tránh flatten object
    } catch {
        Write-Host "⚠️ File config bị lỗi hoặc trống, sẽ tạo mới." -ForegroundColor Yellow
    }
}

# Đảm bảo cấu trúc object
if (-not $ConfigJson.PSObject.Properties["mcpServers"]) {
    $ConfigJson = $ConfigJson | Select-Object *, @{mcpServers = @{}}
}

# Tạo cấu hình cho Server này
$ServerConfig = @{
    command = $VenvPython
    args    = @("$ProjectRoot\openproject-mcp-fastmcp.py")
    env     = @{
        PYTHONPATH          = $ProjectRoot
        OPENPROJECT_URL     = $OpenProjectUrl
        OPENPROJECT_API_KEY = $ApiKey
    }
}

# Thêm/Cập nhật vào config
$ConfigJson.mcpServers | Add-Member -Type NoteProperty -Name "openproject-fastmcp" -Value $ServerConfig -Force

# Lưu file
$ConfigJson | ConvertTo-Json -Depth 10 | Set-Content $ConfigFile -Encoding UTF8

Write-Host "`n✅ CÀI ĐẶT THÀNH CÔNG!" -ForegroundColor Green
Write-Host "Đã cập nhật file config tại: $ConfigFile"
Write-Host "👉 Vui lòng khởi động lại Claude Desktop để bắt đầu sử dụng."
Write-Host "Nhấn phím bất kỳ để thoát..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
