> Instructional guide example, created October 4, 2026. Not attributed to the owner or approved as their voice. Microsoft documentation checked on that date. The small verification exercise below was run in PowerShell 7.6.5; no downloaded release was evaluated.

# Check a file's SHA256 in PowerShell

Have the downloaded file and expected checksum ready. Obtain the checksum from the release publisher's own page. Record which release and file it describes so that a mismatch has a useful starting point for investigation.

## Key takeaways

- Calculate a checksum with `Get-FileHash -Algorithm SHA256` and read the returned object's `Hash` property. [Microsoft's Get-FileHash documentation](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash?view=powershell-7.5).
- Compare it with the publisher's SHA256 for that exact release and filename. Microsoft demonstrates this pattern with a release package. [Microsoft's comparison example](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash?view=powershell-7.5#example-3-compute-the-hash-of-a-stream).

## Calculate and compare the checksum

Open PowerShell. The following prompts ask for the file's full path and expected hexadecimal checksum. Paste the path without surrounding quote characters. The commands read the file and display a comparison; they do not launch it.

```powershell
$articleFile = Read-Host 'Full path to the downloaded file'
$expectedHash = (Read-Host 'Expected SHA256 from the publisher').Trim()
$actualHash = (Get-FileHash -LiteralPath $articleFile -Algorithm SHA256 -ErrorAction Stop).Hash
$actualHash
$actualHash -eq $expectedHash
```

`-LiteralPath` uses the path as written instead of interpreting wildcard characters. That matters for filenames containing square brackets. [Microsoft's parameter definition](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash?view=powershell-7.5#-literalpath).

The last expression asks whether the strings match. A `True` result completes this comparison. Save the release reference alongside the result if you need to explain later which file was checked.

## If the values differ

First compare the filename, version, operating system and architecture with the publisher's checksum entry. Check that the pasted value contains no filename or explanatory label. Run the calculation again after correcting a selection mistake.

If the file still disagrees with the correct entry, stop this procedure there. The comparison found a discrepancy; it did not establish its cause. Retain the expected and actual values before deciding whether to obtain another copy or contact the publisher.

## A small reproducible check

The authoring check used a temporary file containing exactly the three ASCII bytes `abc`, without a newline. PowerShell returned:

```text
BA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD
```

That check exercised calculation and equality in the stated environment. It does not certify another download. For your file, completion means a comparison against the correct publisher-provided value, with the release identity recorded.
