$obj = [PSCustomObject]@{
    text = "\`r`n"
}
$obj | ConvertTo-Json
