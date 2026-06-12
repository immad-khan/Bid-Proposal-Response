using System;
using System.Text;
using System.Threading.Tasks;

namespace BackendNet.Services
{
    public interface IDocumentGenerator
    {
        Task<byte[]> GenerateAsync(string content, string format);
    }

    public class DocumentGenerator : IDocumentGenerator
    {
        public async Task<byte[]> GenerateAsync(string content, string format)
        {
            await Task.Delay(10); // Simulate generation delay
            string documentText = $"--- Generated {format.ToUpper()} Proposal ---\n\n{content}\n\nGenerated at: {DateTime.UtcNow}\n";
            return Encoding.UTF8.GetBytes(documentText);
        }
    }
}
