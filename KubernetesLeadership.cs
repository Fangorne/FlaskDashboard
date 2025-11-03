using k8s;
using k8s.Models;
using System;
using System.Threading;

public class LeaderElector
{
    private readonly string _leaseName = "mon-app-lease";
    private readonly string _namespace = "default";
    private readonly string _podName;
    private readonly Kubernetes _k8sClient;

    public LeaderElector(string podName)
    {
        _podName = podName;
        var config = KubernetesClientConfiguration.BuildDefaultConfig();
        _k8sClient = new Kubernetes(config);
    }

    public bool TryAcquireLeadership()
    {
        try
        {
            // Créer ou mettre à jour le Lease
            var lease = new V1Lease
            {
                Metadata = new V1ObjectMeta
                {
                    Name = _leaseName,
                    Namespace = _namespace
                },
                Spec = new V1LeaseSpec
                {
                    HolderIdentity = _podName,
                    LeaseDurationSeconds = 15,
                    RenewTime = DateTime.UtcNow
                }
            };

            // Essayer de créer le Lease
            var createdLease = _k8sClient.CreateNamespacedLease(lease, _namespace);

            // Si le Lease existe déjà, vérifier si on peut le renouveler
            if (createdLease.Spec.HolderIdentity != _podName)
            {
                Console.WriteLine("Un autre Pod est déjà le leader.");
                return false;
            }

            Console.WriteLine("Je suis le leader !");
            return true;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Erreur lors de l'élection du leader : {ex.Message}");
            return false;
        }
    }

    public void RenewLeadership()
    {
        while (true)
        {
            try
            {
                var lease = _k8sClient.ReadNamespacedLease(_leaseName, _namespace);
                if (lease.Spec.HolderIdentity == _podName)
                {
                    // Renouveler le Lease
                    lease.Spec.RenewTime = DateTime.UtcNow;
                    _k8sClient.ReplaceNamespacedLease(lease, _leaseName, _namespace);
                    Console.WriteLine("Lease renouvelé.");
                }
                else
                {
                    Console.WriteLine("Je ne suis plus le leader.");
                    break;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Erreur lors du renouvellement du Lease : {ex.Message}");
            }
            Thread.Sleep(5000); // Renouveler toutes les 5 secondes
        }
    }
}
