using k8s;
using k8s.LeaderElection;
using k8s.LeaderElection.ResourceLock;
using Microsoft.Extensions.Hosting;
using System.Text;

public class LeaderBackgroundService : BackgroundService
{
    private readonly IKubernetes _client;
    private bool _isLeader = false;

    public LeaderBackgroundService(IKubernetes client)
    {
        _client = client;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        var ns = Environment.GetEnvironmentVariable("POD_NAMESPACE");
        var name = Environment.GetEnvironmentVariable("POD_NAME");

        var resourceLock = new LeaseLock(
            @namespace: ns,
            name: "my-app-leader",
            identity: name,
            client: _client);

        var leaderElection = new LeaderElector(new LeaderElectionConfig(
            lock: resourceLock,
            leaseDuration: TimeSpan.FromSeconds(15),
            renewDeadline: TimeSpan.FromSeconds(10),
            retryPeriod: TimeSpan.FromSeconds(2),
            onStartedLeading: async ct =>
            {
                Console.WriteLine($"✅ I am leader: {name}");
                _isLeader = true;

                await PatchLabelAsync(ns, name, "active");

                while (!ct.IsCancellationRequested)
                    await Task.Delay(1000, ct);
            },
            onStoppedLeading: async () =>
            {
                Console.WriteLine($"❌ Lost leadership: {name}");
                _isLeader = false;
                await PatchLabelAsync(ns, name, null);
            }
        ));

        leaderElection.Run(stoppingToken);
    }

    private async Task PatchLabelAsync(string ns, string pod, string? role)
    {
        var patchJson = role == null
            ? @"{""metadata"":{""labels"":{""role"":null}}}"
            : @"{""metadata"":{""labels"":{""role"":""active""}}}";

        var patch = new V1Patch(patchJson, V1Patch.PatchType.StrategicMergePatch);
        await _client.CoreV1.PatchNamespacedPodAsync(patch, pod, ns);
    }
}




using k8s;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddSingleton<IKubernetes>(_ =>
{
    var config = KubernetesClientConfiguration.InClusterConfig();
    return new Kubernetes(config);
});

builder.Services.AddHostedService<LeaderBackgroundService>();

var app = builder.Build();

app.MapGet("/", () => "App OK");
app.MapGet("/who", () => Environment.GetEnvironmentVariable("POD_NAME"));

app.Run();

```yaml
env:
  - name: POD_NAME
    valueFrom:
      fieldRef:
        fieldPath: metadata.name

  - name: POD_NAMESPACE
    valueFrom:
      fieldRef:
        fieldPath: metadata.namespace
```

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app-service
spec:
  selector:
    app: my-app
    role: active
  ports:
    - name: http
      port: 80
      targetPort: 80
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      serviceAccountName: my-app-sa
      containers:
        - name: web
          image: myacr.io/myapp:latest
          ports:
            - containerPort: 80
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 5
          env:
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
            - name: POD_NAMESPACE
              valueFrom:
                fieldRef:
                  fieldPath: metadata.namespace
```
```yaml
# rbac-leader.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-app-sa
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: my-app-role
  namespace: default
rules:
  # Permet patch/get sur le Pod (pour ajouter/enlever label role=active)
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "patch", "update", "list"]

  # Permet d'utiliser/mettre à jour les Leases pour la leader election
  - apiGroups: ["coordination.k8s.io"]
    resources: ["leases"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: my-app-rb
  namespace: default
subjects:
  - kind: ServiceAccount
    name: my-app-sa
    namespace: default
roleRef:
  kind: Role
  name: my-app-role
  apiGroup: rbac.authorization.k8s.io
```
