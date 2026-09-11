$ErrorActionPreference = "Continue"
$Out = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProgressPreference = "SilentlyContinue"

# TLS + ignore bad certs (some Sci-Hub / campus mirrors)
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
add-type @"
using System.Net;
using System.Security.Cryptography.X509Certificates;
public class TrustAllCertsPolicy : ICertificatePolicy {
    public bool CheckValidationResult(ServicePoint sp, X509Certificate cert, WebRequest req, int problem) { return true; }
}
"@
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy

function Test-Pdf([string]$path) {
    if (-not (Test-Path $path)) { return $false }
    $fs = [IO.File]::OpenRead($path)
    $buf = New-Object byte[] 5
    $n = $fs.Read($buf, 0, 5)
    $fs.Close()
    if ($n -lt 5) { return $false }
    $s = [Text.Encoding]::ASCII.GetString($buf)
    return $s.StartsWith("%PDF")
}

function Get-File([string]$url, [string]$dest) {
    try {
        $headers = @{
            "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            "Accept" = "application/pdf,application/octet-stream,*/*"
        }
        Invoke-WebRequest -Uri $url -OutFile $dest -Headers $headers -TimeoutSec 90 -UseBasicParsing
        if (Test-Pdf $dest) { return $true }
        $len = if (Test-Path $dest) { (Get-Item $dest).Length } else { 0 }
        Write-Host "  not_pdf $len bytes  $url"
        if (Test-Path $dest) { Remove-Item $dest -Force }
        return $false
    } catch {
        Write-Host ("  ERR " + $_.Exception.Message + "  " + $url)
        if (Test-Path $dest) { Remove-Item $dest -Force }
        return $false
    }
}

function Try-Urls([string]$name, [string[]]$urls) {
    $dest = Join-Path $Out $name
    if (Test-Pdf $dest) {
        Write-Host "SKIP $name"
        return
    }
    foreach ($u in $urls) {
        Write-Host "TRY $name"
        Write-Host "  $u"
        if (Get-File $u $dest) {
            Write-Host ("OK  $name  " + (Get-Item $dest).Length)
            return
        }
        Start-Sleep -Milliseconds 400
    }
    Write-Host "FAIL $name"
}

# OA / known public
Try-Urls "Galceran2013_Survey_Coverage_Path_Planning.pdf" @(
    "https://dugi-doc.udg.edu/bitstream/handle/10256/9088/Survey-coverage-path-planning.pdf?sequence=1",
    "https://dugi-doc.udg.edu/bitstream/handle/10256/9088/Survey-coverage-path-planning.pdf?sequence=1&isAllowed=y",
    "https://scispace.com/pdf/a-survey-on-coverage-path-planning-for-robotics-584p6o3a2k.pdf"
)

Try-Urls "Bishop2009_ISSNIP_Sensor_Target_Geometries_RSS.pdf" @(
    "https://www.csc.kth.se/~patric/publications/BishopJensfeltISSNIP09.pdf"
)

Try-Urls "Magers2016_UAV_RF_Emitter_Geolocation_AFIT.pdf" @(
    "https://scholar.afit.edu/cgi/viewcontent.cgi?article=1437&context=etd",
    "https://apps.dtic.mil/sti/pdfs/AD1012071.pdf"
)

Try-Urls "Dogancay2022_Optimal_Geometries_AOA_Bayesian.pdf" @(
    "https://mdpi-res.com/d_attachment/sensors/sensors-22-09802/article_deploy/sensors-22-09802.pdf",
    "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9785418/pdf/sensors-22-09802.pdf",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC9785418/pdf/sensors-22-09802.pdf"
)

# Sci-Hub landing then hope direct pdf
$dois = @(
    @{ Name = "Stansfield1947_Statistical_theory_of_DF_fixing.pdf"; Doi = "10.1049/ji-3a-2.1947.0096" },
    @{ Name = "Dogancay2005_Bearings_Only_TLS.pdf"; Doi = "10.1016/j.sigpro.2005.03.007" },
    @{ Name = "Bishop2010_Optimality_analysis_sensor_target_geometries.pdf"; Doi = "10.1016/j.automatica.2009.12.003" },
    @{ Name = "Xu2017_Optimal_Sensor_Placement_3D_AOA.pdf"; Doi = "10.1109/TAES.2017.2667999" },
    @{ Name = "Dogancay2012_UAV_Path_Planning_Passive_Emitter.pdf"; Doi = "10.1109/TAES.2012.6178054" },
    @{ Name = "Gholami2015_Worst_Case_Position_Error_Bearing_Only.pdf"; Doi = "10.1109/WPNC.2015.7413217" },
    @{ Name = "Ruan2025_UAV_Directional_Emitter_Joint_Estimation.pdf"; Doi = "10.1109/LWC.2024.3519640" },
    @{ Name = "Ruan2023_Multi_Stage_RF_Emitter_Search_Geolocation.pdf"; Doi = "10.1109/TVT.2022.3231398" },
    @{ Name = "Galceran2013_RAS_Survey_CPP.pdf"; Doi = "10.1016/j.robot.2013.09.004" }
)

$hosts = @("sci-hub.ru","sci-hub.st","sci-hub.su","sci-hub.al","sci-hub.ee","sci-hub.mk")

foreach ($job in $dois) {
    $dest = Join-Path $Out $job.Name
    if (Test-Pdf $dest) {
        Write-Host ("SKIP " + $job.Name)
        continue
    }
    Write-Host ("=== " + $job.Name + "  " + $job.Doi + " ===")
    $ok = $false
    foreach ($h in $hosts) {
        $urls = @(
            ("https://{0}/{1}" -f $h, $job.Doi),
            ("https://sci.bban.top/pdf/{0}.pdf" -f $job.Doi)
        )
        foreach ($u in $urls) {
            Write-Host "TRY $u"
            $tmp = Join-Path $Out ("_tmp_" + [Guid]::NewGuid().ToString() + ".bin")
            try {
                Invoke-WebRequest -Uri $u -OutFile $tmp -Headers @{
                    "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
                    "Accept" = "text/html,application/pdf,*/*"
                } -TimeoutSec 50 -UseBasicParsing
            } catch {
                Write-Host ("  ERR " + $_.Exception.Message)
                if (Test-Path $tmp) { Remove-Item $tmp -Force }
                continue
            }
            if (Test-Pdf $tmp) {
                Move-Item $tmp $dest -Force
                Write-Host ("OK  " + $job.Name + "  " + (Get-Item $dest).Length)
                $ok = $true
                break
            }
            # parse iframe
            $html = Get-Content $tmp -Raw -ErrorAction SilentlyContinue
            Remove-Item $tmp -Force -ErrorAction SilentlyContinue
            if (-not $html) { continue }
            $m = [regex]::Matches($html, '(?:iframe|embed)[^>]+src=["'']([^"'']+)["'']', 'IgnoreCase')
            $m2 = [regex]::Matches($html, 'https?://[^"''\s>]+?\.pdf[^"''\s<]*', 'IgnoreCase')
            $cands = @()
            foreach ($x in $m) { $cands += $x.Groups[1].Value }
            foreach ($x in $m2) { $cands += $x.Value }
            foreach ($c in $cands) {
                if ($c.StartsWith("//")) { $c = "https:" + $c }
                elseif ($c.StartsWith("/")) { $c = "https://" + $h + $c }
                Write-Host "  iframe $c"
                if (Get-File $c $dest) {
                    Write-Host ("OK  " + $job.Name + "  " + (Get-Item $dest).Length)
                    $ok = $true
                    break
                }
            }
            if ($ok) { break }
        }
        if ($ok) { break }
    }
    if (-not $ok) { Write-Host ("FAIL " + $job.Name) }
}

Write-Host "DONE"
