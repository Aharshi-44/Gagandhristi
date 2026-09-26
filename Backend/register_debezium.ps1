# PowerShell helper to verify and register Debezium CDC Connector for Gagandristhi V2
$uri = "http://localhost:8083/connectors"
$connectorName = "gagandristhi-alerts-connector"

Write-Host "Connecting to Debezium Kafka Connect at $uri..." -ForegroundColor Cyan

$body = @{
    name = $connectorName
    config = @{
        "connector.class" = "io.debezium.connector.postgresql.PostgresConnector"
        "tasks.max" = "1"
        "plugin.name" = "pgoutput"
        "database.hostname" = "gagandristhi-postgres"
        "database.port" = "5432"
        "database.user" = "postgres"
        "database.password" = "Minar@123"
        "database.dbname" = "garuda"
        "database.server.name" = "garuda_server"
        "topic.prefix" = "garuda_cdc"
        "table.include.list" = "public.alerts"
        "publication.name" = "dbz_publication"
        "publication.autocreate.mode" = "filtered"
        "schema.history.internal.kafka.bootstrap.servers" = "gagandristhi-kafka:29092"
        "schema.history.internal.kafka.topic" = "schema-changes.garuda"
    }
} | ConvertTo-Json -Depth 5

$maxRetries = 15
$count = 0

while ($count -lt $maxRetries) {
    try {
        $existing = Invoke-RestMethod -Uri $uri -Method Get -TimeoutSec 5 -ErrorAction Stop
        if ($existing -contains $connectorName) {
            Write-Host "[OK] Connector '$connectorName' is already registered and active." -ForegroundColor Green
            exit 0
        }
        
        $response = Invoke-RestMethod -Uri $uri -Method Post -ContentType "application/json" -Body $body -ErrorAction Stop
        Write-Host "[OK] Successfully registered '$connectorName'!" -ForegroundColor Green
        exit 0
    } catch {
        $count++
        Write-Host "Waiting for Debezium service to be fully ready ($count/$maxRetries)..." -ForegroundColor Yellow
        Start-Sleep -Seconds 4
    }
}

Write-Host "[WARNING] Timed out waiting for Debezium. Check 'docker logs gagandristhi-debezium'." -ForegroundColor Red
exit 1
