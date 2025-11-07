builder.Services.AddSingleton<IKubernetes>(sp =>
{
    var config = KubernetesClientConfiguration.InClusterConfig();
    return new Kubernetes(config);
});
builder.Services.AddHostedService<LeaderElectionService>();

var app = builder.Build();

var leaderService = app.Services.GetRequiredService<LeaderElectionService>();

app.MapGet("/healthz", () =>
{
    return leaderService.IsLeader
        ? Results.Ok("Leader")
        : Results.StatusCode(503);
});

app.MapGet("/", () => "Hello, I'm alive but not leader.");

app.Run();
