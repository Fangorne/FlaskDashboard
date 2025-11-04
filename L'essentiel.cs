using k8s;
using k8s.Models;
using Microsoft.Extensions.Hosting;
using System;
using System.Threading;
using System.Threading.Tasks;

public class LeaderService : BackgroundService
{
    private readonly IKubernetes _client;
    private readonly string _leaseName = "my-app-leader";
    private readonly string _namespace = "default";
    private readonly string _identity = Environment.GetEnvironmentVariable("HOSTNAME");
    private readonly TimeSpan _leaseDuration = TimeSpan.FromSeconds(15);

    public LeaderService(IKubernetes client)
    {
        _client = client;
    }

    protected override async Task ExecuteAsync(CancellationToken token)
    {
        while (!token.IsCancellationRequested)
        {
            bool isLeader = await TryAcquireOrRenewLease(token);

            if (isLeader)
            {
                Console.WriteLine($"✅ {_identity} is leader — doing work...");
                await Task.Delay(TimeSpan.FromSeconds(5), token); // ton traitement
            }
            else
            {
                Console.WriteLine($"⏸ {_identity} is NOT leader — waiting...");
                await Task.Delay(2000, token);
            }
        }
    }

    private async Task<bool> TryAcquireOrRenewLease(CancellationToken token)
    {
        var now = DateTime.UtcNow;

        try
        {
            // Get or create lease
            var lease = await _client.ReadNamespacedLeaseAsync(_leaseName, _namespace, cancellationToken: token);

            // Si expiré -> n'importe qui peut reprendre
            if (lease.Spec.LeaseDurationSeconds != null &&
                lease.Spec.RenewTime < now.AddSeconds(-lease.Spec.LeaseDurationSeconds.Value))
            {
                return await UpdateLease(lease, token);
            }

            // Si déjà leader → renouvellement
            if (lease.Spec.HolderIdentity == _identity)
            {
                return await UpdateLease(lease, token);
            }

            return false;
        }
        catch (k8s.Autorest.HttpOperationException ex) when (ex.Response.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            // Création du lease si inexistant
            return await CreateLease(token);
        }
    }

    private async Task<bool> CreateLease(CancellationToken token)
    {
        var lease = new V1Lease
        {
            Metadata = new V1ObjectMeta { Name = _leaseName },
            Spec = new V1LeaseSpec
            {
                HolderIdentity = _identity,
                LeaseDurationSeconds = (int)_leaseDuration.TotalSeconds,
                RenewTime = DateTime.UtcNow
            }
        };

        try
        {
            await _client.CreateNamespacedLeaseAsync(lease, _namespace, cancellationToken: token);
            return true;
        }
        catch
        {
            return false;
        }
    }

    private async Task<bool> UpdateLease(V1Lease lease, CancellationToken token)
    {
        lease.Spec.HolderIdentity = _identity;
        lease.Spec.RenewTime = DateTime.UtcNow;

        try
        {
            await _client.ReplaceNamespacedLeaseAsync(lease, _leaseName, _namespace, cancellationToken: token);
            return true;
        }
        catch
        {
            return false;
        }
    }
}
