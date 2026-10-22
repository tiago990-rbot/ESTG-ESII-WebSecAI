param([switch]$VerifyOnly)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()
$backendPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'codigo\backend'
$pythonPath = Join-Path $backendPath '.venv\Scripts\python.exe'
$writerPath = Join-Path $backendPath 'scripts\save_provider_keys.py'

$form = New-Object System.Windows.Forms.Form
$form.Text = 'WebSecAI - configurar fontes e IA'
$form.ClientSize = New-Object System.Drawing.Size(650, 490)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.Font = New-Object System.Drawing.Font('Segoe UI', 10)
$form.BackColor = [System.Drawing.Color]::White

function Add-TextLabel([string]$text, [int]$top, [int]$height) {
    $label = New-Object System.Windows.Forms.Label
    $label.Text = $text
    $label.Location = New-Object System.Drawing.Point(24, $top)
    $label.Size = New-Object System.Drawing.Size(602, $height)
    $form.Controls.Add($label)
}
Add-TextLabel 'Liga a pesquisa, a IA e a fonte opcional URLhaus.' 18 28
Add-TextLabel 'Cria as contas nos portais oficiais. Escolhe os planos gratuitos. Cola aqui apenas as chaves; os campos ficam ocultos e nao sao enviados para o chat.' 54 65
Add-TextLabel 'Chave Tavily - pesquisa publica' 128 24
$tavily = New-Object System.Windows.Forms.TextBox
$tavily.Location = New-Object System.Drawing.Point(24, 155)
$tavily.Size = New-Object System.Drawing.Size(602, 28)
$tavily.UseSystemPasswordChar = $true
$tavily.MaxLength = 512
$form.Controls.Add($tavily)
Add-TextLabel 'Chave Groq - sintese e perguntas por IA' 200 24
$groq = New-Object System.Windows.Forms.TextBox
$groq.Location = New-Object System.Drawing.Point(24, 227)
$groq.Size = New-Object System.Drawing.Size(602, 28)
$groq.UseSystemPasswordChar = $true
$groq.MaxLength = 512
$form.Controls.Add($groq)
Add-TextLabel 'Chave URLhaus - opcional, consulta de malware' 270 24
$urlhaus = New-Object System.Windows.Forms.TextBox
$urlhaus.Location = New-Object System.Drawing.Point(24, 297)
$urlhaus.Size = New-Object System.Drawing.Size(602, 28)
$urlhaus.UseSystemPasswordChar = $true
$urlhaus.MaxLength = 512
$form.Controls.Add($urlhaus)
Add-TextLabel 'Campos vazios preservam as chaves existentes e as restantes configuracoes. Guardar nao faz chamadas externas.' 342 48
$free = New-Object System.Windows.Forms.CheckBox
$free.Text = 'Confirmo que escolhi planos gratuitos, sem faturacao ativa.'
$free.Location = New-Object System.Drawing.Point(24, 402)
$free.Size = New-Object System.Drawing.Size(602, 28)
$form.Controls.Add($free)
$save = New-Object System.Windows.Forms.Button
$save.Text = 'Guardar no projeto'
$save.Location = New-Object System.Drawing.Point(420, 445)
$save.Size = New-Object System.Drawing.Size(206, 32)
$form.Controls.Add($save)
$cancel = New-Object System.Windows.Forms.Button
$cancel.Text = 'Fechar'
$cancel.Location = New-Object System.Drawing.Point(292, 445)
$cancel.Size = New-Object System.Drawing.Size(112, 32)
$cancel.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
$form.Controls.Add($cancel)
$form.AcceptButton = $save
$form.CancelButton = $cancel
$save.Add_Click({
    if (-not $free.Checked) {
        [System.Windows.Forms.MessageBox]::Show('Confirma os planos gratuitos antes de guardar.', 'WebSecAI') | Out-Null
        return
    }
    if ([string]::IsNullOrWhiteSpace($tavily.Text) -and [string]::IsNullOrWhiteSpace($groq.Text) -and [string]::IsNullOrWhiteSpace($urlhaus.Text)) {
        [System.Windows.Forms.MessageBox]::Show('Introduz pelo menos uma chave.', 'WebSecAI') | Out-Null
        return
    }
    $process = $null
    try {
        $save.Enabled = $false
        $info = New-Object System.Diagnostics.ProcessStartInfo
        $info.FileName = $pythonPath
        $info.Arguments = '"' + $writerPath + '"'
        $info.WorkingDirectory = $backendPath
        $info.UseShellExecute = $false
        $info.CreateNoWindow = $true
        $info.RedirectStandardInput = $true
        $info.RedirectStandardOutput = $true
        $info.RedirectStandardError = $true
        $process = [System.Diagnostics.Process]::Start($info)
        # Credentials travel only through stdin, never shell history or process arguments.
        $payload = @{ TAVILY_API_KEY = $tavily.Text; GROQ_API_KEY = $groq.Text; URLHAUS_AUTH_KEY = $urlhaus.Text } | ConvertTo-Json -Compress
        $process.StandardInput.Write($payload)
        $process.StandardInput.Close()
        $payload = $null
        if (-not $process.WaitForExit(10000)) {
            $process.Kill()
            throw 'Timeout'
        }
        if ($process.ExitCode -ne 0) { throw 'Save failed' }
        $tavily.Clear()
        $groq.Clear(); $urlhaus.Clear()
        [System.Windows.Forms.MessageBox]::Show('Configuracao guardada. Diz no chat apenas que ja guardaste, para reiniciar o backend e verificar as ligacoes. Nao envies as chaves.', 'WebSecAI') | Out-Null
        $form.Close()
    } catch {
        # No exception text or child output: they could contain private data.
        [System.Windows.Forms.MessageBox]::Show('Nao foi possivel guardar. Confirma que colaste apenas as chaves e que o ambiente local existe. Nenhuma chave foi enviada para o chat.', 'WebSecAI') | Out-Null
    } finally {
        if ($null -ne $process) { $process.Dispose() }
        $save.Enabled = $true
    }
})
if ($VerifyOnly) {
    if (-not ($tavily.UseSystemPasswordChar -and $groq.UseSystemPasswordChar -and $urlhaus.UseSystemPasswordChar -and $tavily.MaxLength -eq 512)) { throw 'Invalid private fields' }
    if (-not ((Test-Path -LiteralPath $writerPath) -and (Test-Path -LiteralPath $pythonPath))) { throw 'Missing local runtime' }
    $form.Dispose()
    Write-Output 'Formulario validado sem mostrar janela, ler chaves ou alterar configuracao.'
} else {
    try { [void]$form.ShowDialog() } finally { $tavily.Clear(); $groq.Clear(); $urlhaus.Clear(); $form.Dispose() }
}
