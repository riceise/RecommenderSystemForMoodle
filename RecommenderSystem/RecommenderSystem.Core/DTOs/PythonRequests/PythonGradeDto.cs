using System.Text.Json.Serialization;


namespace RecommenderSystem.Core.DTOs.PythonRequests;

public class PythonGradeDto
{
    [JsonPropertyName("ItemName")]
    public string ItemName { get; set; } = string.Empty;

    [JsonPropertyName("RawGrade")]
    public double RawGrade { get; set; }

    [JsonPropertyName("MaxGrade")]
    public double MaxGrade { get; set; }

    [JsonPropertyName("CourseTags")]
    public List<string> CourseTags { get; set; } = new();
}