# PowerShell Script to Sync Project to GitHub
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Pushing UK Top 50 Analytics Suite to rintathomas2027/ukanalysis" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan

Set-Location -Path $PSScriptRoot

if (-not (Test-Path -Path ".git")) {
    Write-Host "Initializing Git repository..." -ForegroundColor Yellow
    git init
    git branch -M main
}

Write-Host "Configuring remote origin..." -ForegroundColor Yellow
git remote remove origin 2>$null
git remote add origin https://github.com/rintathomas2027/ukanalysis.git

Write-Host "Staging files..." -ForegroundColor Yellow
git add .

Write-Host "Committing changes..." -ForegroundColor Yellow
git commit -m "feat: complete UK Top 50 playlist market structure, artist diversity & content localization analysis suite"

Write-Host "Pushing to GitHub main branch..." -ForegroundColor Yellow
git push -u origin main

Write-Host "Synchronization complete! Visit https://github.com/rintathomas2027/ukanalysis" -ForegroundColor Green
