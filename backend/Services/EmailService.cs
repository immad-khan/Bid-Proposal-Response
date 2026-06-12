using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace BackendNet.Services
{
    public interface IEmailService
    {
        Task SendInviteEmail(string email, string inviteId);
    }

    public class EmailService : IEmailService
    {
        private readonly ILogger<EmailService> _logger;

        public EmailService(ILogger<EmailService> logger)
        {
            _logger = logger;
        }

        public async Task SendInviteEmail(string email, string inviteId)
        {
            await Task.Delay(10); // Simulate network delay
            _logger.LogInformation($"[EMAIL MOCK] Sending invitation email to {email} with inviteId: {inviteId}");
        }
    }
}
