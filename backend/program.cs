using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using System.Text;
using BackendNet.Data;
using BackendNet.Services;
using BackendNet.Models;

var builder = WebApplication.CreateBuilder(args);

// ✅ Load .env file for local 'dotnet run' execution
var rootDir = Directory.GetParent(Directory.GetCurrentDirectory())?.FullName;
var envPath = Path.Combine(rootDir ?? "", ".env");
if (File.Exists(envPath))
{
    foreach (var line in File.ReadAllLines(envPath))
    {
        var parts = line.Split('=', 2, StringSplitOptions.RemoveEmptyEntries);
        if (parts.Length == 2 && !line.TrimStart().StartsWith("#"))
        {
            Environment.SetEnvironmentVariable(parts[0].Trim(), parts[1].Trim());
        }
    }
}
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

// ✅ CORS — reads ALLOWED_ORIGINS from env; falls back to open if not set
var allowedOriginsEnv = Environment.GetEnvironmentVariable("ALLOWED_ORIGINS");
var hasExplicitOrigins = !string.IsNullOrWhiteSpace(allowedOriginsEnv);
var allowedOrigins = hasExplicitOrigins
    ? allowedOriginsEnv!.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
    : Array.Empty<string>();

builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowFrontend", policy =>
    {
        if (hasExplicitOrigins)
        {
            // Production: restrict to known frontend origins
            policy.WithOrigins(allowedOrigins)
                  .AllowAnyMethod()
                  .AllowAnyHeader()
                  .AllowCredentials();
        }
        else
        {
            // Dev / Azure before ALLOWED_ORIGINS is set: open CORS so app stays up
            policy.AllowAnyOrigin()
                  .AllowAnyMethod()
                  .AllowAnyHeader();
        }
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

// Database is assumed to be created via migrations in production.
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
    db.Database.EnsureCreated();
}

// ✅ Swagger enabled in all environments for testing
app.UseSwagger();
app.UseSwaggerUI();

// ✅ Root health check endpoint
app.MapGet("/", () => new { service = "RFP Backend API", status = "running", swagger = "/swagger" });

// ✅ CORS diagnostic endpoint — call this from browser to verify CORS is working
app.MapGet("/cors-check", (HttpContext ctx) => new {
    status = "cors_ok",
    service = "net-api",
    origin = ctx.Request.Headers["Origin"].ToString(),
    timestamp = DateTime.UtcNow.ToString("o")
}).RequireCors("AllowFrontend");

// ✅ CORS must be before Authentication/Authorization
app.UseCors("AllowFrontend");

app.UseAuthentication();
app.UseAuthorization();

// ✅ Map Controllers
app.MapControllers();

app.Run();