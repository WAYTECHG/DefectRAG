param()
$ErrorActionPreference='Stop'
$galleryRoot=Split-Path $PSScriptRoot -Parent
$galleryFolder=Join-Path $galleryRoot 'runtime/gallery-setup'
New-Item -ItemType Directory -Force -Path $galleryFolder | Out-Null
$galleryKeyFile=Join-Path $galleryFolder 'gallery-key.txt'
if(Test-Path -LiteralPath $galleryKeyFile){
    $galleryKey=[IO.File]::ReadAllText($galleryKeyFile).Trim()
    if($galleryKey -notmatch '^[a-f0-9]{64}$'){throw 'Existing gallery key is invalid. It was preserved.'}
}else{
    $galleryBytes=New-Object byte[] 32
    $galleryRandom=[Security.Cryptography.RandomNumberGenerator]::Create()
    try{$galleryRandom.GetBytes($galleryBytes)}finally{$galleryRandom.Dispose()}
    $galleryKey=([BitConverter]::ToString($galleryBytes)).Replace('-','').ToLowerInvariant()
    [IO.File]::WriteAllText($galleryKeyFile,$galleryKey)
}
$gallerySql=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'supabase_public_gallery.sql'))
$gallerySql+="`nselect public.defectrag_gallery_configure('$galleryKey');`n"
$gallerySqlFile=Join-Path $galleryFolder 'gallery-setup.sql'
[IO.File]::WriteAllText($gallerySqlFile,$gallerySql)
Write-Output "Prepared local setup SQL: $gallerySqlFile"
Write-Output "Private gallery key file: $galleryKeyFile"
Write-Output 'Review the SQL and execute it manually in Supabase SQL Editor.'
Write-Output 'Set HF Space secret DEFECTRAG_GALLERY_KEY to the key file content, and variable DEFECTRAG_GALLERY_ENABLED to 1.'
Write-Output 'Keep runtime/ private. No database, deployment settings or existing staff records were changed.'
