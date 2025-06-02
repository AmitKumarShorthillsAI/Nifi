import org.apache.commons.io.IOUtils
import java.nio.charset.StandardCharsets
import groovy.json.JsonOutput
import groovy.json.JsonSlurper

flowFile = session.get()
if (!flowFile) return

flowFile = session.write(flowFile, { inputStream, outputStream ->
    def inputText = IOUtils.toString(inputStream, StandardCharsets.UTF_8)
    def jsonParser = new JsonSlurper()
    def record = jsonParser.parseText(inputText)  // SINGLE RECORD, not list

    // Add new field 'sum' = value1 + value2
    record.sum = (record.value1 ?: 0) + (record.value2 ?: 0)

    def result = JsonOutput.toJson(record)
    outputStream.write(result.getBytes(StandardCharsets.UTF_8))
} as StreamCallback)

session.transfer(flowFile, REL_SUCCESS)