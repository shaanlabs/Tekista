$files = @(
    "ADMIN_ANALYTICS.md",
    "AI_ASSISTANT.md",
    "AI_FEATURES.md",
    "AI_SETUP_GUIDE.md",
    "AUTOMATION_SUMMARY.md",
    "COMPLETE_PROJECT_SUMMARY.md",
    "ENTERPRISE_FEATURES.md",
    "ENTERPRISE_SETUP.md",
    "ENTERPRISE_SUMMARY.md",
    "IMPLEMENTATION_SUMMARY.md",
    "INTEGRATION_GUIDE.md",
    "MCP_SERVER_GUIDE.md",
    "MODERN_UI_DESIGN.md",
    "NOTIFICATIONS_SYSTEM.md",
    "PERFORMANCE_SERVICE.md",
    "PERFORMANCE_SUMMARY.md",
    "QUICK_REFERENCE.md",
    "RECOMMENDATION_SYSTEM.md",
    "SKILLS_MANAGEMENT.md",
    "SKILL_ASSIGNMENT_SUMMARY.md",
    "SKILL_BASED_ASSIGNMENT.md",
    "SYSTEM_INTEGRATION_SUMMARY.md",
    "TASK_AUTOMATION.md"
)

foreach ($file in $files) {
    $source = "c:\tekista-project\$file"
    $dest = "c:\tekista-project\docs\"
    if (Test-Path $source) {
        Move-Item -Path $source -Destination $dest -Force
        Write-Host "Moved: $file"
    }
}

Write-Host "All files moved successfully!"
