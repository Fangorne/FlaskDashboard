

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
