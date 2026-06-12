using System;
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.IdentityModel.Tokens;

namespace BackendNet.Services
{
    public interface IAuthService
    {
        Task<bool> ValidateUserAsync(string username, string password);
        Task<string> GenerateTokenAsync(string username);
    }

    public class AuthService : IAuthService
    {
        private readonly IConfiguration _configuration;

        public AuthService(IConfiguration configuration)
        {
            _configuration = configuration;
        }

        public async Task<bool> ValidateUserAsync(string username, string password)
        {
            // Simple credential verification (extendable to database query)
            await Task.Delay(10);
            return username == "admin" && password == "password";
        }

        public async Task<string> GenerateTokenAsync(string username)
        {
            await Task.Delay(10);

            var jwtKey = _configuration["Jwt:Key"] ?? "SUPER_SECRET_SECURITY_KEY_FOR_JWT_AUTHENTICATION_32_BYTES_LONG";
            var issuer = _configuration["Jwt:Issuer"] ?? "BidProposalResponseIssuer";
            var audience = _configuration["Jwt:Audience"] ?? "BidProposalResponseAudience";

            var tokenHandler = new JwtSecurityTokenHandler();
            var key = Encoding.UTF8.GetBytes(jwtKey);

            var tokenDescriptor = new SecurityTokenDescriptor
            {
                Subject = new ClaimsIdentity(new[]
                {
                    new Claim(ClaimTypes.Name, username),
                    new Claim(ClaimTypes.Role, "Admin")
                }),
                Expires = DateTime.UtcNow.AddHours(4),
                Issuer = issuer,
                Audience = audience,
                SigningCredentials = new SigningCredentials(
                    new SymmetricSecurityKey(key),
                    SecurityAlgorithms.HmacSha256Signature
                )
            };

            var token = tokenHandler.CreateToken(tokenDescriptor);
            return tokenHandler.WriteToken(token);
        }
    }
}
