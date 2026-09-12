# Diagnostic script for Cloudflare environment (deterministic probe)
$ErrorActionPreference = "SilentlyContinue"

$result = [ordered]@{
    timestamp = (Get-Date).ToString("o")
    node = [ordered]@{
        installed = $false
        version = $null
    }
    wrangler = [ordered]@{
        installed = $false
        version = $null
        authenticated = $false
        authType = $null
        email = $null
        accountId = $null
        accountName = $null
    }
    cloudflared = [ordered]@{
        installed = $false
        version = $null
    }
    env = [ordered]@{
        hasApiToken = (![string]::IsNullOrEmpty($env:CLOUDFLARE_API_TOKEN))
        hasAccountId = (![string]::IsNullOrEmpty($env:CLOUDFLARE_ACCOUNT_ID))
    }
}

# 1. Check Node.js
try {
    $nodeVer = node -v 2>$null
    if ($nodeVer) {
        $result.node.installed = $true
        $result.node.version = $nodeVer.Trim()
    }
} catch {}

# 2. Check Wrangler
try {
    $wranglerVer = npx --yes wrangler --version 2>$null
    if ($wranglerVer) {
        $result.wrangler.installed = $true
        $result.wrangler.version = ($wranglerVer | Select-Object -Last 1).Trim()

        # Check whoami
        $whoamiRaw = npx --yes wrangler whoami 2>$null | Out-String
        if ($whoamiRaw -match "logged in with an?\s+([^,\.]+)") {
            $result.wrangler.authenticated = $true
            $result.wrangler.authType = $matches[1].Trim()
        }
        if ($whoamiRaw -match "([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})") {
            $result.wrangler.email = $matches[1].Trim()
        }
        
        $lines = $whoamiRaw -split "`r?`n"
        foreach ($line in $lines) {
            if ($line -match "([a-f0-9]{32})") {
                $result.wrangler.accountId = $matches[1].Trim()
                # Clean line from borders and extract name before the 32-hex id
                $cleaned = $line -replace "[^a-zA-Z0-9\s@\.\'-]", " "
                if ($cleaned -match "^\s*([a-zA-Z0-9\s@\.\'-]+?)\s+([a-f0-9]{32})") {
                    $nameCandidate = $matches[1].Trim()
                    if ($nameCandidate -and $nameCandidate -notmatch "Account Name") {
                        $result.wrangler.accountName = $nameCandidate
                    }
                }
            }
        }
    }
} catch {}

# 3. Check Cloudflared
try {
    $cfVer = cloudflared --version 2>$null
    if ($cfVer -match "cloudflared version\s+([^\s]+)") {
        $result.cloudflared.installed = $true
        $result.cloudflared.version = $matches[1].Trim()
    }
} catch {}

# Output pure JSON
$result | ConvertTo-Json -Depth 5
