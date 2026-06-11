var builder = WebApplication.CreateBuilder(args);

// ✅ Add Controllers
builder.Services.AddControllers();

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

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

// ✅ CORS must be before MapControllers
app.UseCors("AllowReactApp");

// ✅ Map Controllers
app.MapControllers();

app.Run();