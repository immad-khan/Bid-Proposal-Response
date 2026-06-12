using System;
using System.Net;
using System.Net.Mail;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration;

namespace BackendNet.Services
{
    public interface IEmailService
    {
        Task SendInviteEmail(string email, string inviteId);
    }

    public class EmailService : IEmailService
    {
        private readonly ILogger<EmailService> _logger;
        private readonly IConfiguration _configuration;

        public EmailService(ILogger<EmailService> logger, IConfiguration configuration)
        {
            _logger = logger;
            _configuration = configuration;
        }

        public async Task SendInviteEmail(string email, string inviteId)
        {
            try
            {
                var host = Environment.GetEnvironmentVariable("EMAIL_HOST") ?? _configuration["Email:Host"];
                var portStr = Environment.GetEnvironmentVariable("EMAIL_PORT") ?? _configuration["Email:Port"];
                var user = Environment.GetEnvironmentVariable("EMAIL_HOST_USER") ?? _configuration["Email:User"];
                var pass = Environment.GetEnvironmentVariable("EMAIL_HOST_PASSWORD") ?? _configuration["Email:Password"];
                var fromName = Environment.GetEnvironmentVariable("EMAIL_FROM_NAME") ?? _configuration["Email:FromName"] ?? "RFP Pilot";

                if (string.IsNullOrEmpty(host) || string.IsNullOrEmpty(user) || string.IsNullOrEmpty(pass))
                {
                    _logger.LogWarning($"[EMAIL] Missing SMTP configuration. Falling back to mock for {email}");
                    return;
                }

                int port = int.TryParse(portStr, out int p) ? p : 587;

                using var client = new SmtpClient(host, port)
                {
                    Credentials = new NetworkCredential(user, pass),
                    EnableSsl = true
                };

                var fromAddress = new MailAddress(user, fromName);
                var toAddress = new MailAddress(email);

                using var message = new MailMessage(fromAddress, toAddress)
                {
                    Subject = "You've been invited to collaborate on an RFP Proposal",
                    Body = $"<p>Hello,</p><p>You have been invited to join a workspace.</p><p>Click <a href='http://localhost:3000/invite/{inviteId}'>here</a> to accept the invitation.</p>",
                    IsBodyHtml = true
                };

                await client.SendMailAsync(message);
                _logger.LogInformation($"[EMAIL] Successfully sent invitation email to {email}");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"[EMAIL ERROR] Failed to send email to {email}");
            }
        }
    }
}
