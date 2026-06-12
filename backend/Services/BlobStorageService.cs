using System;
using System.IO;
using System.Threading.Tasks;
using Azure.Storage.Blobs;
using Azure.Storage.Blobs.Models;
using Microsoft.Extensions.Configuration;

namespace BackendNet.Services
{
    public interface IBlobStorageService
    {
        Task<string> UploadFileAsync(Stream fileStream, string fileName, string contentType);
        Task<Stream> DownloadFileAsync(string blobUrl);
        Task<string> UploadGeneratedFileAsync(string fileName, byte[] bytes);
    }

    public class BlobStorageService : IBlobStorageService
    {
        private readonly BlobServiceClient? _blobServiceClient;
        private const string ContainerName = "rfp-uploads";

        public BlobStorageService(IConfiguration configuration)
        {
            var connectionString = configuration["AzureStorage:ConnectionString"];
            if (!string.IsNullOrEmpty(connectionString) && connectionString != "YOUR_AZURE_STORAGE_CONNECTION_STRING_HERE" && connectionString != "your_azure_storage_connection_string_here")
            {
                _blobServiceClient = new BlobServiceClient(connectionString);
            }
        }

        public async Task<string> UploadFileAsync(Stream fileStream, string fileName, string contentType)
        {
            if (_blobServiceClient == null)
            {
                var fakeUrl = $"http://localhost:5000/mock-storage/{Guid.NewGuid()}_{fileName}";
                return fakeUrl;
            }

            var containerClient = _blobServiceClient.GetBlobContainerClient(ContainerName);
            await containerClient.CreateIfNotExistsAsync(PublicAccessType.None);

            var uniqueFileName = $"{Guid.NewGuid()}_{fileName}";
            var blobClient = containerClient.GetBlobClient(uniqueFileName);

            var blobHttpHeaders = new BlobHttpHeaders { ContentType = contentType };
            await blobClient.UploadAsync(fileStream, new BlobUploadOptions { HttpHeaders = blobHttpHeaders });

            return blobClient.Uri.ToString();
        }

        public async Task<Stream> DownloadFileAsync(string blobUrl)
        {
            if (_blobServiceClient == null)
            {
                return new MemoryStream(System.Text.Encoding.UTF8.GetBytes("Mock file content"));
            }

            var uri = new Uri(blobUrl);
            var blobClient = new BlobClient(uri);
            var response = await blobClient.DownloadStreamingAsync();
            return response.Value.Content;
        }

        public async Task<string> UploadGeneratedFileAsync(string fileName, byte[] bytes)
        {
            using var stream = new MemoryStream(bytes);
            return await UploadFileAsync(stream, fileName, "application/octet-stream");
        }
    }
}
