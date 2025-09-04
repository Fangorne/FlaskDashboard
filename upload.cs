
using Microsoft.Extensions.Logging;
using Xunit;
using Xunit.Abstractions;

public class LoggerAdapter<T> : ILogger<T>, IDisposable
{
    private readonly ITestOutputHelper _output;

    public LoggerAdapter(ITestOutputHelper output)
    {
        _output = output;
    }

    public IDisposable BeginScope<TState>(TState state) => this;

    public void Dispose() { }

    public bool IsEnabled(LogLevel logLevel) => true;

    public void Log<TState>(
        LogLevel logLevel,
        EventId eventId,
        TState state,
        Exception exception,
        Func<TState, Exception, string> formatter)
    {
        _output.WriteLine($"{logLevel}: {formatter(state, exception)}");
    }
}

public class DemoTests
{
    private readonly ILogger<DemoTests> _logger;

    public DemoTests(ITestOutputHelper output)
    {
        _logger = new LoggerAdapter<DemoTests>(output);
    }

    [Fact]
    public void Test1()
    {
        _logger.LogInformation("Début du test {Test}", nameof(Test1));
        Assert.True(1 + 1 == 2);
        _logger.LogInformation("Fin du test {Test}", nameof(Test1));
    }
}


public async Task UploadFileManualAsync()
{
    string accessKey = "TA_CLEF_ACCES";
    string secretKey = "TON_SECRET";
    string region = "eu-fr2";
    string bucket = "mon-bucket";
    string objectKey = "test.txt";
    string filePath = "chemin/local/vers/test.txt";
    string service = "s3";
    string host = $"{bucket}.s3.{region}.cloud-object-storage.appdomain.cloud";
    string endpoint = $"https://{host}/{objectKey}";

    var fileBytes = File.ReadAllBytes(filePath);
    var contentSha256 = ToHex(SHA256.HashData(fileBytes));

    var now = DateTime.UtcNow;
    var amzDate = now.ToString("yyyyMMddTHHmmssZ");
    var dateStamp = now.ToString("yyyyMMdd");

    string credentialScope = $"{dateStamp}/{region}/{service}/aws4_request";
    string canonicalRequest =
        $"PUT\n/{objectKey}\n\n" +
        $"host:{host}\n" +
        $"x-amz-content-sha256:{contentSha256}\n" +
        $"x-amz-date:{amzDate}\n\n" +
        $"host;x-amz-content-sha256;x-amz-date\n" +
        $"{contentSha256}";

    string stringToSign =
        $"AWS4-HMAC-SHA256\n{amzDate}\n{credentialScope}\n" +
        $"{ToHex(SHA256.HashData(Encoding.UTF8.GetBytes(canonicalRequest)))}";

    byte[] signingKey = GetSignatureKey(secretKey, dateStamp, region, service);
    byte[] signatureBytes = HmacSHA256(signingKey, stringToSign);
    string signature = ToHex(signatureBytes);

    string authorizationHeader =
        $"AWS4-HMAC-SHA256 Credential={accessKey}/{credentialScope}, " +
        $"SignedHeaders=host;x-amz-content-sha256;x-amz-date, Signature={signature}";

    using var httpClient = new HttpClient();
    var request = new HttpRequestMessage(HttpMethod.Put, endpoint)
    {
        Content = new ByteArrayContent(fileBytes)
    };

    request.Headers.Add("x-amz-date", amzDate);
    request.Headers.Add("x-amz-content-sha256", contentSha256);
    request.Headers.Add("Authorization", authorizationHeader);

    var response = await httpClient.SendAsync(request);
    Console.WriteLine($"{(int)response.StatusCode} {response.ReasonPhrase}");
    if (!response.IsSuccessStatusCode)
    {
        Console.WriteLine(await response.Content.ReadAsStringAsync());
    }
}

byte[] HmacSHA256(byte[] key, string data)
{
    using var hmac = new HMACSHA256(key);
    return hmac.ComputeHash(Encoding.UTF8.GetBytes(data));
}

byte[] GetSignatureKey(string key, string dateStamp, string regionName, string serviceName)
{
    byte[] kSecret = Encoding.UTF8.GetBytes("AWS4" + key);
    byte[] kDate = HmacSHA256(kSecret, dateStamp);
    byte[] kRegion = HmacSHA256(kDate, regionName);
    byte[] kService = HmacSHA256(kRegion, serviceName);
    byte[] kSigning = HmacSHA256(kService, "aws4_request");
    return kSigning;
}

string ToHex(byte[] data)
{
    return BitConverter.ToString(data).Replace("-", "").ToLower();
}


var md5Hash = MD5.HashData(fileBytes);
string contentMD5 = Convert.ToBase64String(md5Hash);

string canonicalHeaders =
    $"content-md5:{contentMD5}\n" +
    $"host:{host}\n" +
    $"x-amz-content-sha256:{contentSha256}\n" +
    $"x-amz-date:{amzDate}\n";

string signedHeaders = "content-md5;host;x-amz-content-sha256;x-amz-date";


string canonicalRequest =
    $"PUT\n/{objectKey}\n\n" +
    canonicalHeaders + "\n" +
    signedHeaders + "\n" +
    contentSha256;

string authorizationHeader =
    $"AWS4-HMAC-SHA256 Credential={accessKey}/{credentialScope}, " +
    $"SignedHeaders={signedHeaders}, Signature={signature}";

request.Headers.Add("Content-MD5", contentMD5);




SELECT 
    r.session_id,
    r.status,
    r.start_time,
    r.command,
    r.cpu_time,
    r.total_elapsed_time / 1000 AS ElapsedSeconds,
    r.wait_type,
    DB_NAME(r.database_id) AS DatabaseName,
    OBJECT_NAME(st.objectid, r.database_id) AS ProcedureName,
    SUBSTRING(st.text, r.statement_start_offset / 2 + 1, 
              (CASE r.statement_end_offset 
               WHEN -1 THEN DATALENGTH(st.text)
               ELSE r.statement_end_offset END 
               - r.statement_start_offset) / 2 + 1) AS RunningStatement,
    st.text AS FullBatch
FROM 
    sys.dm_exec_requests r
JOIN 
    sys.dm_exec_sessions s ON r.session_id = s.session_id
CROSS APPLY 
    sys.dm_exec_sql_text(r.sql_handle) st
WHERE 
    s.is_user_process = 1
ORDER BY 
    r.total_elapsed_time DESC;


SELECT 
    r.session_id,
    qp.query_plan
FROM 
    sys.dm_exec_requests r
CROSS APPLY 
    sys.dm_exec_query_plan(r.plan_handle) qp
WHERE 
    r.session_id = <ID_session_à_cibler>
