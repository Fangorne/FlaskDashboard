public async IAsyncEnumerable<T> ReadObjectsByBlockAsync<T>(
    string path, int blockSize = 10 * 1024 * 1024,  // 10 Mo
    [System.Runtime.CompilerServices.EnumeratorCancellation] CancellationToken ct = default)
{
    byte[] buffer = new byte[blockSize];
    using var fs = File.OpenRead(path);
    int bytesRead;

    var reader = new MessagePackStreamReader(fs);
    List<T> batch = new();

    while ((bytesRead = await fs.ReadAsync(buffer, 0, buffer.Length, ct)) > 0)
    {
        var seq = new ReadOnlySequence<byte>(buffer.AsMemory(0, bytesRead));
        var msgReader = new MessagePackReader(seq);

        while (!msgReader.End)
        {
            var obj = MessagePackSerializer.Deserialize<T>(ref msgReader);
            batch.Add(obj);
            if (batch.Count >= 1000) // ex. 1000 objets
            {
                foreach (var item in batch)
                    yield return item;
                batch.Clear();
            }
        }
    }

    foreach (var item in batch)
        yield return item;
}
