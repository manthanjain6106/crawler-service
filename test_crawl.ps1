# PowerShell script to test the crawler service
Write-Host "Testing Crawler Service..."

# Test health endpoint
Write-Host "`n1. Testing health endpoint..."
try {
    $healthResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
    Write-Host "Health check: $($healthResponse.StatusCode)"
    Write-Host "Response: $($healthResponse.Content)"
} catch {
    Write-Host "Health check failed: $($_.Exception.Message)"
    exit 1
}

# Test crawl endpoint
Write-Host "`n2. Testing crawl endpoint..."
$crawlBody = @{
    url = "https://en.wikipedia.org/wiki/Main_Page"
    max_depth = 1
    follow_links = $false
    extract_text = $true
    extract_images = $true
    extract_links = $true
    extract_headings = $true
    extract_image_alt_text = $true
    extract_canonical_url = $true
} | ConvertTo-Json

$headers = @{
    'Content-Type' = 'application/json'
}

try {
    $crawlResponse = Invoke-WebRequest -Uri "http://localhost:8000/crawl" -Method POST -Body $crawlBody -Headers $headers -UseBasicParsing
    Write-Host "Crawl request: $($crawlResponse.StatusCode)"
    $crawlResult = $crawlResponse.Content | ConvertFrom-Json
    Write-Host "Task ID: $($crawlResult.task_id)"
    Write-Host "Status: $($crawlResult.status)"
    
    # Wait a bit for processing
    Write-Host "`n3. Waiting for crawl to complete..."
    Start-Sleep -Seconds 10
    
    # Check task status
    Write-Host "`n4. Checking task status..."
    $taskResponse = Invoke-WebRequest -Uri "http://localhost:8000/crawl/$($crawlResult.task_id)" -UseBasicParsing
    $taskResult = $taskResponse.Content | ConvertFrom-Json
    Write-Host "Task Status: $($taskResult.status)"
    
    if ($taskResult.status -eq "completed") {
        # Get results
        Write-Host "`n5. Getting crawl results..."
        $resultResponse = Invoke-WebRequest -Uri "http://localhost:8000/crawl/$($crawlResult.task_id)/result" -UseBasicParsing
        $result = $resultResponse.Content | ConvertFrom-Json
        Write-Host "Total pages: $($result.total_pages)"
        Write-Host "Duration: $($result.duration) seconds"
        
        if ($result.pages -and $result.pages.Count -gt 0) {
            $firstPage = $result.pages[0]
            Write-Host "`nFirst page details:"
            Write-Host "URL: $($firstPage.url)"
            Write-Host "Title: $($firstPage.title)"
            Write-Host "Status Code: $($firstPage.status_code)"
            Write-Host "Images: $($firstPage.images.Count)"
            Write-Host "Links: $($firstPage.links.Count)"
        }
    }
    
} catch {
    Write-Host "Crawl request failed: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Error details: $responseBody"
    }
}

Write-Host "`nTest completed."
