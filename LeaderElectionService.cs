using k8s;
using k8s.Models;
using System;
using System.Threading;
using System.Threading.Tasks;

public class LeaderElectionService : BackgroundService
{
    private readonly IKubernetes _client;
    private readonly string _podName;
    private readonly string _namespace;
    private readonly string _leaseName = "my-app-leader";

    public bool IsLeader { get; private set; }

    public LeaderElectionService(IKubernetes client)
    {
        _client = client;
        _podName = Environment.GetEnvironmentVariable("POD_NAME");
        _namespace = Environment.GetEnvironmentVariable("POD_NAMESPACE");
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                await TryAcquireLease(stoppingToken);
            }
            catch (Exception ex)
            {
                Console.WriteLine("Lease error: " + ex.Message);
            }

            await Task.Delay(TimeSpan.FromSeconds(3), stoppingToken);
        }
    }

    private async Task TryAcquireLease(CancellationToken ct)
    {
        var lease = await _client.CoordinationV1.ReadNamespacedLeaseAsync(_leaseName, _namespace, cancellationToken: ct);

        var now = DateTimeOffset.UtcNow;
        var expiredTime = lease.Spec.RenewTime?.AddSeconds(lease.Spec.LeaseDurationSeconds ?? 10);

        bool leaseExpired = expiredTime == null || expiredTime < now;

        if (lease.Spec.HolderIdentity == _podName || leaseExpired)
        {
            // Renew the lease
            lease.Spec.HolderIdentity = _podName;
            lease.Spec.AcquireTime = now;
            lease.Spec.RenewTime = now;

            await _client.CoordinationV1.ReplaceNamespacedLeaseAsync(lease, _leaseName, _namespace, cancellationToken: ct);
            IsLeader = true;
        }
        else
        {
            IsLeader = false;
        }
    }
}
