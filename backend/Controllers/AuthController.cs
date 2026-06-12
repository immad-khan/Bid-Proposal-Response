using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using BackendNet.Services;

namespace BackendNet.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class AuthController : ControllerBase
    {
        private readonly IAuthService _authService;

        public AuthController(IAuthService authService)
        {
            _authService = authService;
        }

        [HttpPost("login")]
        public async Task<IActionResult> Login([FromBody] LoginRequest request)
        {
            if (request == null || string.IsNullOrEmpty(request.Username) || string.IsNullOrEmpty(request.Password))
            {
                return BadRequest(new { error = "Username and password are required." });
            }

            var isValid = await _authService.ValidateUserAsync(request.Username, request.Password);
            if (!isValid)
            {
                return Unauthorized(new { error = "Invalid credentials." });
            }

            var token = await _authService.GenerateTokenAsync(request.Username);
            return Ok(new { token });
        }
    }

    public class LoginRequest
    {
        public string Username { get; set; } = string.Empty;
        public string Password { get; set; } = string.Empty;
    }
}
