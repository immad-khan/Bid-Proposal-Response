using System.IO;
using System.Threading.Tasks;

namespace BackendNet.Services
{
    public interface IBlobStorageService
    {
        Task<string> UploadFileAsync(Stream fileStream, string fileName, string contentType);
        Task<Stream> DownloadFileAsync(string blobUrl);
    }

    public class BlobStorageService : IBlobStorageService
    {
        public async Task<string> UploadFileAsync(Stream fileStream, string fileName, string contentType)
        {
            await Task.Delay(50);
            return $"https://mockstorage.blob.core.windows.net/rfp-uploads/{fileName}";
        }

        public async Task<Stream> DownloadFileAsync(string blobUrl)
        {
            await Task.Delay(50);
            return new MemoryStream();
        }
    }
}
