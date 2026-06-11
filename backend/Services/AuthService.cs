using System.Threading.Tasks;

namespace BackendNet.Services
{
    public interface IAuthService
    {
        Task<bool> ValidateUserAsync(string username, string password);
        Task<string> GenerateTokenAsync(string username);
    }

    public class AuthService : IAuthService
    {
        public async Task<bool> ValidateUserAsync(string username, string password)
        {
            // Placeholder auth logic
            await Task.Delay(10);
            return username == "admin" && password == "password";
        }

        public async Task<string> GenerateTokenAsync(string username)
        {
            await Task.Delay(10);
            return $"mock-jwt-token-for-{username}";
        }
    }
}
