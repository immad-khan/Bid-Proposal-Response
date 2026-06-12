using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using System.Text;
using BackendNet.Data;
using BackendNet.Services;
using BackendNet.Models;

var builder = WebApplication.CreateBuilder(args);

// ✅ Add DbContext with SQLite
builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlite(builder.Configuration.GetConnectionString("DefaultConnection") ?? "Data Source=rfp.db"));

// ✅ Add Controllers
builder.Services.AddControllers();

// ✅ JWT Authentication configuration
var jwtKey = builder.Configuration["Jwt:Key"] ?? "SUPER_SECRET_SECURITY_KEY_FOR_JWT_AUTHENTICATION_32_BYTES_LONG";
var issuer = builder.Configuration["Jwt:Issuer"] ?? "BidProposalResponseIssuer";
var audience = builder.Configuration["Jwt:Audience"] ?? "BidProposalResponseAudience";

builder.Services.AddAuthentication(options =>
{
    options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
})
.AddJwtBearer(options =>
{
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuer = true,
        ValidateAudience = true,
        ValidateLifetime = true,
        ValidateIssuerSigningKey = true,
        ValidIssuer = issuer,
        ValidAudience = audience,
        IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtKey))
    };
});

builder.Services.AddAuthorization();

// ✅ Custom Services DI
builder.Services.AddSingleton<IAuthService, AuthService>();
builder.Services.AddScoped<IBlobStorageService, BlobStorageService>();
builder.Services.AddSingleton<IProjectManagementService, ProjectManagementService>();
builder.Services.AddScoped<IDashboardService, DashboardService>();
builder.Services.AddScoped<IWorkspaceService, WorkspaceService>();
builder.Services.AddScoped<IEmailService, EmailService>();
builder.Services.AddScoped<IDocumentGenerator, DocumentGenerator>();

// ✅ HttpClient (built into .NET 10, no extra package needed)
builder.Services.AddHttpClient();

// ✅ CORS for React/Vercel
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowReactApp", policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

// ✅ File upload size limit
builder.Services.Configure<Microsoft.AspNetCore.Http.Features.FormOptions>(options =>
{
    options.MultipartBodyLengthLimit = 104857600; // 100 MB
});

// ✅ Swagger
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// ✅ Auto-create database & Seed Mock Data
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
    db.Database.EnsureCreated();

    // Seed User
    if (!db.Users.Any())
    {
        db.Users.AddRange(
            new User { Id = "admin", Username = "admin", Email = "admin@example.com" },
            new User { Id = "member1", Username = "jane_doe", Email = "jane@example.com" }
        );
        db.SaveChanges();
    }

    // Seed Projects
    if (!db.Projects.Any())
    {
        var p1 = new Project
        {
            Id = "nasa-rfp",
            Name = "NASA Deep Space Communication System",
            ClientName = "NASA Jet Propulsion Lab",
            SubmissionDeadline = DateTime.UtcNow.AddDays(30),
            SimilarPastWinRate = 0.85,
            OwnerId = "admin"
        };
        p1.Members.Add(new ProjectMember { ProjectId = "nasa-rfp", UserId = "admin" });
        p1.Members.Add(new ProjectMember { ProjectId = "nasa-rfp", UserId = "member1" });

        var p2 = new Project
        {
            Id = "dod-cloud",
            Name = "Pentagon secure Cloud Migration",
            ClientName = "US Department of Defense",
            SubmissionDeadline = DateTime.UtcNow.AddDays(15),
            SimilarPastWinRate = 0.55,
            OwnerId = "admin"
        };
        p2.Members.Add(new ProjectMember { ProjectId = "dod-cloud", UserId = "admin" });

        var p3 = new Project
        {
            Id = "who-system",
            Name = "Global Health Informatics Upgrade",
            ClientName = "World Health Organization",
            SubmissionDeadline = DateTime.UtcNow.AddDays(45),
            SimilarPastWinRate = 0.25,
            OwnerId = "admin"
        };
        p3.Members.Add(new ProjectMember { ProjectId = "who-system", UserId = "admin" });

        db.Projects.AddRange(p1, p2, p3);
        db.SaveChanges();
    }

    // Seed Workspaces
    if (!db.Workspaces.Any())
    {
        var w1 = new Workspace
        {
            Id = "nasa-rfp", // matches Project Id for routing convenience
            Name = "NASA Deep Space Communication System Workspace",
            Description = "Collaboration workspace for RFP engineering response to NASA JPL.",
            OwnerId = "admin",
            CreatedAt = DateTime.UtcNow.AddDays(-2),
            UpdatedAt = DateTime.UtcNow
        };
        
        w1.Members.Add(new WorkspaceMember { WorkspaceId = "nasa-rfp", UserId = "admin", Role = "Admin" });
        w1.Members.Add(new WorkspaceMember { WorkspaceId = "nasa-rfp", UserId = "member1", Role = "Editor" });
        
        var jsonVal1 = "[{\"type\":\"paragraph\",\"children\":[{\"text\":\"Draft v1: Developing high-efficiency deep space transceiver. Design limits power consumption to 20W.\"}]}]";
        var jsonVal2 = "[{\"type\":\"paragraph\",\"children\":[{\"text\":\"Draft v2: NASA Deep Space Communication System Proposal. Section 1: Introduction. We propose a cognitive radio system operating in the Ka-band. Performance metrics exceed JPL specifications by 15%.\"}]}]";

        w1.Versions.Add(new ProposalVersion
        {
            Id = Guid.NewGuid().ToString(),
            WorkspaceId = "nasa-rfp",
            VersionNumber = 1,
            Content = jsonVal1,
            CreatedBy = "admin",
            CreatedAt = DateTime.UtcNow.AddDays(-2),
            Comment = "Initial layout and technical summary"
        });

        w1.Versions.Add(new ProposalVersion
        {
            Id = Guid.NewGuid().ToString(),
            WorkspaceId = "nasa-rfp",
            VersionNumber = 2,
            Content = jsonVal2,
            CreatedBy = "member1",
            CreatedAt = DateTime.UtcNow.AddDays(-1),
            Comment = "Added section 1.1 with Ka-band specifications"
        });

        db.Workspaces.Add(w1);
        db.SaveChanges();
    }
}

// ✅ Swagger enabled in all environments for testing
app.UseSwagger();
app.UseSwaggerUI();

// ✅ Root health check endpoint
app.MapGet("/", () => new { service = "RFP Backend API", status = "running", swagger = "/swagger" });

// ✅ CORS must be before Authentication/Authorization
app.UseCors("AllowReactApp");

app.UseAuthentication();
app.UseAuthorization();

// ✅ Map Controllers
app.MapControllers();

app.Run();