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

using var fs = File.OpenRead("data.msgpack");
var seq = new ReadOnlySequence<byte>(File.ReadAllBytes("data.msgpack"));
var reader = new MessagePackReader(seq);
int count = reader.ReadArrayHeader();

for (int i = 0; i < count; i++)
{
    var obj = MessagePackSerializer.Deserialize<MyType>(ref reader);
    // Traiter obj ici
}


using var fs = File.OpenRead(path);
var buffer = new byte[8192];
int read;
var sequence = new Sequence<byte>();

while ((read = await fs.ReadAsync(buffer, 0, buffer.Length)) > 0)
{
    sequence.Write(buffer.AsMemory(0, read));
    var reader = new MessagePackReader(sequence.AsReadOnlySequence);

    while (TryReadOne(ref reader, out MyType obj))
    {
        yield return obj;
    }

    sequence = new Sequence<byte>(sequence.AsReadOnlySequence.Slice(reader.Consumed));
}


public async IAsyncEnumerable<T> ReadStreamingAsync<T>(string path, int bufferSize = 8192, [System.Runtime.CompilerServices.EnumeratorCancellation] CancellationToken ct = default)
{
    await using var fs = File.OpenRead(path);

    var buffer = new byte[bufferSize];
    var leftover = new MemoryStream();

    int read;

    while ((read = await fs.ReadAsync(buffer, 0, buffer.Length, ct)) > 0)
    {
        leftover.Write(buffer, 0, read);

        var seq = new ReadOnlySequence<byte>(leftover.GetBuffer(), 0, (int)leftover.Length);

        // ✅ MessagePackReader hors async / hors iterator
        var items = DeserializeMany<T>(seq, out var consumed);

        foreach (var item in items)
            yield return item;

        // garder le reste
        var remaining = leftover.Length - consumed;
        if (remaining > 0)
            Array.Copy(leftover.GetBuffer(), consumed, leftover.GetBuffer(), 0, remaining);

        leftover.SetLength(remaining);
    }
}

private static IEnumerable<T> DeserializeMany<T>(ReadOnlySequence<byte> seq, out long consumed)
{
    var reader = new MessagePackReader(seq);
    var result = new List<T>();
    consumed = 0;

    while (!reader.End)
    {
        try
        {
            result.Add(MessagePackSerializer.Deserialize<T>(ref reader));
            consumed = reader.Consumed;
        }
        catch
        {
            break;
        }
    }

    return result;
}


public IEnumerable<T> ReadStreaming<T>(string path, int bufferSize = 8192)
{
    using var fs = File.OpenRead(path);

    var buffer = new byte[bufferSize];
    var leftover = new MemoryStream();

    int read;

    while ((read = fs.Read(buffer, 0, buffer.Length)) > 0)
    {
        leftover.Write(buffer, 0, read);

        var seq = new ReadOnlySequence<byte>(leftover.GetBuffer(), 0, (int)leftover.Length);
        var reader = new MessagePackReader(seq);

        long consumed = 0;

        while (!reader.End)
        {
            try
            {
                var item = MessagePackSerializer.Deserialize<T>(ref reader);
                consumed = reader.Consumed;
                yield return item;
            }
            catch
            {
                break; // message incomplet → lire plus de données
            }
        }

        // garder la partie non consommée
        var remaining = leftover.Length - consumed;
        if (remaining > 0)
            Array.Copy(leftover.GetBuffer(), consumed, leftover.GetBuffer(), 0, remaining);

        leftover.SetLength(remaining);
    }
}
