// Copyright project_phoenix
package com.project_phoenix.project_phoenix

import android.Manifest
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.os.Build
import android.os.ParcelFileDescriptor
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.annotation.RequiresApi
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.Image
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Settings
import android.content.Context
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import androidx.compose.foundation.shape.RoundedCornerShape
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import com.chaquo.python.PyObject
import android.content.pm.PackageManager
import android.media.AudioFormat
import android.media.MediaCodec
import android.media.MediaExtractor
import android.media.MediaFormat
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull
import kotlinx.coroutines.suspendCancellableCoroutine
import androidx.core.content.ContextCompat
import java.io.File
import java.io.FileOutputStream
import android.provider.OpenableColumns
import android.webkit.MimeTypeMap
import androidx.compose.material.icons.filled.Info
import kotlin.coroutines.resume

private val VIDEO_EXTENSIONS = setOf("mp4", "mov", "m4v", "avi", "mkv", "webm", "3gp")
private val AUDIO_EXTENSIONS = setOf("wav", "mp3", "m4a", "aac", "ogg", "flac")
private const val TRANSCRIPTION_TIMEOUT_MS = 120_000L

private fun mediaKindFromExtension(path: String): String? {
    val ext = path.substringAfterLast('.', "").lowercase()
    return when {
        ext in VIDEO_EXTENSIONS -> "video"
        ext in AUDIO_EXTENSIONS -> "audio"
        else -> null
    }
}

private fun safeDelete(path: String?) {
    if (path.isNullOrBlank()) return
    runCatching { File(path).delete() }
}

private fun speechRecognizerErrorLabel(error: Int): String = when (error) {
    SpeechRecognizer.ERROR_AUDIO -> "audio input failure"
    SpeechRecognizer.ERROR_CLIENT -> "client error"
    SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "insufficient permissions"
    SpeechRecognizer.ERROR_LANGUAGE_NOT_SUPPORTED -> "language not supported"
    SpeechRecognizer.ERROR_LANGUAGE_UNAVAILABLE -> "language unavailable"
    SpeechRecognizer.ERROR_NETWORK -> "network error"
    SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "network timeout"
    SpeechRecognizer.ERROR_NO_MATCH -> "no speech match"
    SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "recognizer busy"
    SpeechRecognizer.ERROR_SERVER -> "server error"
    SpeechRecognizer.ERROR_SERVER_DISCONNECTED -> "server disconnected"
    SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "speech timeout"
    SpeechRecognizer.ERROR_TOO_MANY_REQUESTS -> "too many requests"
    SpeechRecognizer.ERROR_CANNOT_CHECK_SUPPORT -> "cannot check support"
    else -> "unknown error"
}

private fun queryDisplayName(context: Context, uri: Uri): String? {
    val projection = arrayOf(OpenableColumns.DISPLAY_NAME)
    return context.contentResolver.query(uri, projection, null, null, null)?.use { cursor ->
        val nameIndex = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
        if (nameIndex >= 0 && cursor.moveToFirst()) cursor.getString(nameIndex) else null
    }
}

private fun guessExtension(context: Context, uri: Uri, displayName: String?): String {
    val fileNameExtension = displayName
        ?.substringAfterLast('.', "")
        ?.takeIf { it.isNotBlank() }

    if (fileNameExtension != null) {
        return ".${fileNameExtension.lowercase()}"
    }

    val mimeType = context.contentResolver.getType(uri) ?: return ""
    val mimeExtension = MimeTypeMap.getSingleton().getExtensionFromMimeType(mimeType)
    return mimeExtension?.let { ".${it.lowercase()}" } ?: ""
}

private fun createTempDocumentCopy(context: Context, uri: Uri): File {
    val displayName = queryDisplayName(context, uri)
    val extension = guessExtension(context, uri, displayName)
    val rawBaseName = displayName?.substringBeforeLast('.', displayName) ?: "temp_doc"
    val sanitizedBaseName = rawBaseName
        .replace(Regex("[^A-Za-z0-9._-]"), "_")
        .ifBlank { "temp_doc" }
        .take(40)
    val prefix = sanitizedBaseName.padEnd(3, '_')
    val tempFile = File.createTempFile(prefix, extension, context.cacheDir)

    context.contentResolver.openInputStream(uri)?.use { input ->
        tempFile.outputStream().use { output -> input.copyTo(output) }
    } ?: throw IllegalStateException("Unable to open the selected document.")

    return tempFile
}

private data class NativeTranscriptResult(
    val text: String,
    val engine: String?,
    val errors: List<String>
)

private data class DecodedPcmAudio(
    val file: File,
    val sampleRate: Int,
    val channelCount: Int
)

private fun decodeMediaAudioToPcm(context: Context, mediaPath: String): DecodedPcmAudio? {
    val extractor = MediaExtractor()
    var codec: MediaCodec? = null
    var outputFile: File? = null
    try {
        extractor.setDataSource(mediaPath)
        var audioTrack = -1
        var inputFormat: MediaFormat? = null
        for (i in 0 until extractor.trackCount) {
            val format = extractor.getTrackFormat(i)
            val mime = format.getString(MediaFormat.KEY_MIME) ?: continue
            if (mime.startsWith("audio/")) {
                audioTrack = i
                inputFormat = format
                break
            }
        }
        if (audioTrack == -1 || inputFormat == null) return null

        extractor.selectTrack(audioTrack)
        val mime = inputFormat.getString(MediaFormat.KEY_MIME) ?: return null
        codec = MediaCodec.createDecoderByType(mime)
        codec.configure(inputFormat, null, null, 0)
        codec.start()

        outputFile = File.createTempFile("media_pcm_", ".pcm", context.cacheDir)
        FileOutputStream(outputFile).use { output ->
            val bufferInfo = MediaCodec.BufferInfo()
            var inputDone = false
            var outputDone = false
            val timeoutUs = 10_000L

            while (!outputDone) {
                if (!inputDone) {
                    val inputIndex = codec.dequeueInputBuffer(timeoutUs)
                    if (inputIndex >= 0) {
                        val inputBuffer = codec.getInputBuffer(inputIndex)
                        if (inputBuffer != null) {
                            val sampleSize = extractor.readSampleData(inputBuffer, 0)
                            if (sampleSize < 0) {
                                codec.queueInputBuffer(
                                    inputIndex,
                                    0,
                                    0,
                                    0,
                                    MediaCodec.BUFFER_FLAG_END_OF_STREAM
                                )
                                inputDone = true
                            } else {
                                val presentationTimeUs = extractor.sampleTime
                                codec.queueInputBuffer(inputIndex, 0, sampleSize, presentationTimeUs, 0)
                                extractor.advance()
                            }
                        }
                    }
                }

                val outputIndex = codec.dequeueOutputBuffer(bufferInfo, timeoutUs)
                when {
                    outputIndex == MediaCodec.INFO_TRY_AGAIN_LATER -> Unit
                    outputIndex == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED -> Unit
                    outputIndex >= 0 -> {
                        val outputBuffer = codec.getOutputBuffer(outputIndex)
                        if (outputBuffer != null && bufferInfo.size > 0) {
                            outputBuffer.position(bufferInfo.offset)
                            outputBuffer.limit(bufferInfo.offset + bufferInfo.size)
                            val chunk = ByteArray(bufferInfo.size)
                            outputBuffer.get(chunk)
                            output.write(chunk)
                        }
                        codec.releaseOutputBuffer(outputIndex, false)
                        if ((bufferInfo.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM) != 0) {
                            outputDone = true
                        }
                    }
                }
            }
        }

        val outputFormat = runCatching { codec.outputFormat }.getOrNull()
        val sampleRate = outputFormat?.getInteger(MediaFormat.KEY_SAMPLE_RATE)
            ?: inputFormat.getInteger(MediaFormat.KEY_SAMPLE_RATE)
        val channelCount = outputFormat?.getInteger(MediaFormat.KEY_CHANNEL_COUNT)
            ?: inputFormat.getInteger(MediaFormat.KEY_CHANNEL_COUNT)

        return DecodedPcmAudio(
            file = outputFile,
            sampleRate = sampleRate,
            channelCount = channelCount
        )
    } catch (_: Exception) {
        outputFile?.delete()
        return null
    } finally {
        runCatching { codec?.stop() }
        runCatching { codec?.release() }
        runCatching { extractor.release() }
    }
}

@RequiresApi(Build.VERSION_CODES.TIRAMISU)
private suspend fun transcribeMediaWithAndroidSpeech(
    context: Context,
    mediaPath: String
): NativeTranscriptResult {
    if (!SpeechRecognizer.isRecognitionAvailable(context)) {
        return NativeTranscriptResult("", null, listOf("Android speech recognizer not available on this device."))
    }

    val pcm = decodeMediaAudioToPcm(context, mediaPath)
        ?: return NativeTranscriptResult("", null, listOf("Failed to decode media audio to PCM for Android speech recognition."))

    val timedResult = withTimeoutOrNull(TRANSCRIPTION_TIMEOUT_MS) {
        withContext(Dispatchers.Main) {
        suspendCancellableCoroutine { continuation ->
            // The on-device recognizer service is crashing on this target device during
            // prerecorded-media transcription, so use the standard recognizer path.
            val recognizer = SpeechRecognizer.createSpeechRecognizer(context)
            val pfd = runCatching {
                ParcelFileDescriptor.open(pcm.file, ParcelFileDescriptor.MODE_READ_ONLY)
            }.getOrNull()

            if (pfd == null) {
                pcm.file.delete()
                recognizer.destroy()
                continuation.resume(NativeTranscriptResult("", null, listOf("Unable to open PCM audio for transcription.")))
                return@suspendCancellableCoroutine
            }

            val collected = mutableListOf<String>()
            var finished = false

            fun finish(result: NativeTranscriptResult) {
                if (finished) return
                finished = true
                runCatching { pfd.close() }
                runCatching { pcm.file.delete() }
                runCatching { recognizer.destroy() }
                continuation.resume(result)
            }

            recognizer.setRecognitionListener(object : RecognitionListener {
                override fun onReadyForSpeech(params: Bundle?) = Unit
                override fun onBeginningOfSpeech() = Unit
                override fun onRmsChanged(rmsdB: Float) = Unit
                override fun onBufferReceived(buffer: ByteArray?) = Unit
                override fun onEndOfSpeech() = Unit
                override fun onEvent(eventType: Int, params: Bundle?) = Unit
                override fun onEndOfSegmentedSession() {
                    val transcript = collected.joinToString(" ").trim()
                    if (transcript.isBlank()) {
                        finish(NativeTranscriptResult("", null, listOf("Android speech recognizer produced no segments.")))
                    } else {
                        finish(NativeTranscriptResult(transcript, "android-speechrecognizer", emptyList()))
                    }
                }

                override fun onPartialResults(partialResults: Bundle?) {
                    val options = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION).orEmpty()
                    if (options.isNotEmpty()) {
                        val candidate = options.first().trim()
                        if (candidate.isNotBlank()) collected.add(candidate)
                    }
                }

                override fun onSegmentResults(segmentResults: Bundle) {
                    val options = segmentResults.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION).orEmpty()
                    if (options.isNotEmpty()) {
                        val candidate = options.first().trim()
                        if (candidate.isNotBlank()) collected.add(candidate)
                    }
                }

                override fun onResults(results: Bundle?) {
                    val options = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION).orEmpty()
                    if (options.isNotEmpty()) {
                        val candidate = options.first().trim()
                        if (candidate.isNotBlank()) collected.add(candidate)
                    }
                    val transcript = collected.joinToString(" ").trim()
                    if (transcript.isBlank()) {
                        finish(NativeTranscriptResult("", null, listOf("Android speech recognizer returned no transcript.")))
                    } else {
                        finish(NativeTranscriptResult(transcript, "android-speechrecognizer", emptyList()))
                    }
                }

                override fun onError(error: Int) {
                    finish(
                        NativeTranscriptResult(
                            "",
                            null,
                            listOf(
                                "Android speech recognizer failed: ${speechRecognizerErrorLabel(error)} (code $error). " +
                                    "If this is prerecorded media, the device speech service may not support file-fed transcription reliably."
                            )
                        )
                    )
                }
            })

            val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
                putExtra(RecognizerIntent.EXTRA_AUDIO_SOURCE, pfd)
                putExtra(RecognizerIntent.EXTRA_AUDIO_SOURCE_CHANNEL_COUNT, pcm.channelCount.coerceAtLeast(1))
                putExtra(RecognizerIntent.EXTRA_AUDIO_SOURCE_ENCODING, AudioFormat.ENCODING_PCM_16BIT)
                putExtra(RecognizerIntent.EXTRA_AUDIO_SOURCE_SAMPLING_RATE, pcm.sampleRate.coerceAtLeast(8000))
            }

            runCatching { recognizer.startListening(intent) }
                .onFailure {
                    finish(NativeTranscriptResult("", null, listOf("Failed to start Android speech recognizer: ${it.message}")))
                }

            continuation.invokeOnCancellation {
                runCatching { recognizer.cancel() }
                runCatching { recognizer.destroy() }
                runCatching { pfd.close() }
                runCatching { pcm.file.delete() }
            }
        }
    }
    }

    return timedResult ?: NativeTranscriptResult(
        "",
        null,
        listOf("Android speech transcription timed out after ${TRANSCRIPTION_TIMEOUT_MS / 1000}s.")
    )
}

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }
        setContent {
            MaterialTheme(colorScheme = DisclosureColorScheme) {
                Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
                    AnalyzerScreen()
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AnalyzerScreen() {
    val context = LocalContext.current
    val uiScope = rememberCoroutineScope()
    var textToAnalyze by remember { mutableStateOf("") }
    var resultData by remember { mutableStateOf<PyObject?>(null) }
    var isLoading by remember { mutableStateOf(false) }
    var statusMessage by remember { mutableStateOf("Ready") }
    var showNoticeDialog by remember { mutableStateOf(false) }
    var selectedMediaPath by remember { mutableStateOf<String?>(null) }
    var selectedMediaKind by remember { mutableStateOf<String?>(null) }
    var manualTranscriptText by remember { mutableStateOf("") }
    val hasRecordAudioPermission = remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.RECORD_AUDIO
            ) == PackageManager.PERMISSION_GRANTED
        )
    }

    val recordPermissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        hasRecordAudioPermission.value = granted
        if (!granted) {
            statusMessage = "Microphone permission denied. Media auto-transcription may fail on this device."
        }
    }
    
    val sharedPreferences = context.getSharedPreferences("phoenix_prefs", Context.MODE_PRIVATE)
    var apiKey by remember { mutableStateOf(sharedPreferences.getString("canlii_api_key", "") ?: "") }

    fun performAnalysis(text: String) {
        if (text.isBlank() && selectedMediaPath == null) return
        isLoading = true
        statusMessage = if (selectedMediaPath != null) "Analyzing media evidence..." else "Analyzing document..."
        uiScope.launch {
            try {
                var nativeTranscriptFailed = false
                var audioTranPath: String? = null
                val results = withContext(Dispatchers.IO) {
                    val py = Python.getInstance()
                    val analyzer = py.getModule("charter_analyzer").callAttr("CharterAnalyzer", apiKey)
                    if (selectedMediaPath != null) {
                        val mediaPath = selectedMediaPath
                        val kind = selectedMediaKind
                        val videoArg: String? = if (kind == "video") mediaPath else null
                        val audioArg: String? = if (kind == "audio") mediaPath else null
                        var nativeTranscript = ""
                        val nativeErrors = mutableListOf<String>()
                        val transcriptOverride = manualTranscriptText.trim()
                        if (mediaPath != null
                            && hasRecordAudioPermission.value
                            && Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU
                            && transcriptOverride.isBlank()
                        ) {
                            val native = transcribeMediaWithAndroidSpeech(context, mediaPath)
                            nativeTranscript = native.text
                            nativeErrors.addAll(native.errors)
                        } else if (mediaPath != null) {
                            when {
                                transcriptOverride.isNotBlank() -> nativeErrors.add(
                                    "Used manual transcript override instead of device auto-transcription."
                                )
                                !hasRecordAudioPermission.value -> nativeErrors.add(
                                    "RECORD_AUDIO permission is not granted. On this Android build, prerecorded media transcription will not start without it."
                                )
                                Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU -> nativeErrors.add(
                                    "Prerecorded audio transcription requires Android 13 or newer on this build."
                                )
                            }
                        }
                        val effectiveTranscript = if (transcriptOverride.isNotBlank()) transcriptOverride else nativeTranscript
                        if (effectiveTranscript.isBlank() && nativeErrors.isNotEmpty()) {
                            throw IllegalStateException(
                                "Audio transcription failed on this device. Paste transcript text into 'Transcript Override' and retry."
                            )
                        }
                        nativeTranscriptFailed = nativeTranscript.isBlank() && transcriptOverride.isBlank() && nativeErrors.isNotEmpty()
                        analyzer.callAttr(
                            "analyze_av_against_witness",
                            text,
                            videoArg,
                            audioArg,
                            effectiveTranscript,
                            nativeErrors.toTypedArray()
                        )
                    } else {
                        analyzer.callAttr("analyze_document", text)
                    }
                }
                if (selectedMediaPath != null) {
                    audioTranPath = withContext(Dispatchers.IO) {
                        writeAudioTranFile(context, results)
                    }
                }
                resultData = results
                statusMessage = when {
                    selectedMediaPath == null -> "Analysis completed"
                    nativeTranscriptFailed -> "Media analysis completed, but transcription failed. Saved audiotran: ${audioTranPath.orEmpty()}"
                    else -> "Media analysis completed. Saved audiotran: ${audioTranPath.orEmpty()}"
                }
            } catch (e: Exception) {
                statusMessage = "Analysis failed: " + e.message
            } finally {
                isLoading = false
            }
        }
    }

    LaunchedEffect(Unit) {
        withContext(Dispatchers.IO) {
            try {
                val py = Python.getInstance()
                py.getModule("initializer").callAttr("initialize_nlp", context.filesDir.absolutePath)
            } catch (e: Exception) {}
        }
    }

    val filePickerLauncher = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        uri?.let {
            isLoading = true
            uiScope.launch {
                try {
                    val loadResult = withContext(Dispatchers.IO) {
                        val tempFile = createTempDocumentCopy(context, uri)
                        val mediaKind = mediaKindFromExtension(tempFile.name)
                        if (mediaKind != null) {
                            mapOf(
                                "mode" to "media",
                                "mediaPath" to tempFile.absolutePath,
                                "mediaKind" to mediaKind,
                                "text" to textToAnalyze
                            )
                        } else {
                            val py = Python.getInstance()
                            val res = py.getModule("document_processor")
                                .callAttr("DocumentProcessor")
                                .callAttr("extract_all_text", tempFile.absolutePath)
                            val resMap: Map<PyObject?, PyObject?> = res.asMap()
                            val builtins = py.getModule("builtins")
                            val errorKey = builtins.callAttr("str", "error")
                            val textKey = builtins.callAttr("str", "text")
                            val errorMessage = resMap[errorKey]?.toString()
                            if (!errorMessage.isNullOrBlank()) {
                                throw IllegalStateException(errorMessage)
                            }

                            val extractedText = resMap[textKey]?.toString()?.trim().orEmpty()
                            if (extractedText.isBlank()) {
                                throw IllegalStateException("No text could be extracted from the selected document.")
                            }

                            tempFile.delete()
                            mapOf(
                                "mode" to "document",
                                "mediaPath" to "",
                                "mediaKind" to "",
                                "text" to extractedText
                            )
                        }
                    }
                    if (loadResult["mode"] == "media") {
                        safeDelete(selectedMediaPath)
                        selectedMediaPath = loadResult["mediaPath"] ?: ""
                        selectedMediaKind = loadResult["mediaKind"] ?: ""
                        manualTranscriptText = ""
                        resultData = null
                        statusMessage = if (hasRecordAudioPermission.value) {
                            "Media loaded (${selectedMediaKind}). Enter supporting statement. If auto-transcription fails, paste transcript override."
                        } else {
                            "Media loaded (${selectedMediaKind}). Enable mic permission or paste transcript override before Analyze."
                        }
                    } else {
                        safeDelete(selectedMediaPath)
                        selectedMediaPath = null
                        selectedMediaKind = null
                        manualTranscriptText = ""
                        textToAnalyze = loadResult["text"] ?: ""
                        resultData = null
                        statusMessage = "Loaded successfully"
                    }
                } catch (e: Exception) {
                    statusMessage = "Load failed: " + e.message
                } finally {
                    isLoading = false
                }
            }
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Column(modifier = Modifier.fillMaxSize()) {
            HeroHeader()
            Spacer(Modifier.height(12.dp))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                FilledTonalButton(onClick = { showNoticeDialog = true }) {
                    Icon(Icons.Default.Info, contentDescription = "Notice")
                    Spacer(Modifier.width(8.dp))
                    Text("Notice")
                }
            }
            Spacer(Modifier.height(12.dp))
            if (resultData == null) {
                Card(
                    modifier = Modifier.fillMaxSize(),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                    shape = RoundedCornerShape(20.dp)
                ) {
                    Column(modifier = Modifier.padding(16.dp).fillMaxSize()) {
                        OutlinedTextField(
                            value = textToAnalyze,
                            onValueChange = { textToAnalyze = it },
                            label = { Text(if (selectedMediaPath != null) "Supporting Statement / Claim Text" else "Report Text") },
                            modifier = Modifier.fillMaxWidth().weight(if (selectedMediaPath != null) 0.58f else 1f)
                        )
                        if (selectedMediaPath != null) {
                            Spacer(Modifier.height(12.dp))
                            OutlinedTextField(
                                value = manualTranscriptText,
                                onValueChange = { manualTranscriptText = it },
                                label = { Text("Transcript Override") },
                                supportingText = {
                                    Text("Paste transcript text here if device audio transcription fails.")
                                },
                                modifier = Modifier.fillMaxWidth().weight(0.42f)
                            )
                        }
                        Spacer(Modifier.height(16.dp))
                        Row(Modifier.fillMaxWidth(), Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { filePickerLauncher.launch("*/*") }, Modifier.weight(1f)) { Text("Open File") }
                            Button(onClick = { performAnalysis(textToAnalyze) }, enabled = !isLoading && (textToAnalyze.isNotBlank() || selectedMediaPath != null), modifier = Modifier.weight(1f)) {
                                if (isLoading) CircularProgressIndicator(Modifier.size(20.dp)) else Text("Analyze")
                            }
                        }
                        if (selectedMediaPath != null && !hasRecordAudioPermission.value) {
                            Spacer(Modifier.height(8.dp))
                            OutlinedButton(onClick = { recordPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO) }) {
                                Text("Enable Mic Permission")
                            }
                        }
                        Spacer(Modifier.height(10.dp))
                        Text(statusMessage, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            } else {
                ResultView(resultData!!, textToAnalyze, { performAnalysis(it) }) { resultData = null }
            }
        }

        if (showNoticeDialog) {
            AlertDialog(
                onDismissRequest = { showNoticeDialog = false },
                confirmButton = {
                    TextButton(onClick = { showNoticeDialog = false }) { Text("Close") }
                },
                title = { Text("Distribution Notice") },
                text = {
                    Text(
                        "Developer contact: kalilife666@gmail.com\n\n" +
                        "Open source software available for free download for all Canadians without a law license. " +
                        "This software is intended to remain available for free download permanently. " +
                        "Contributions to the developers and their descendants are welcome via e-Transfer to kalilife666@gmail.com. " +
                        "Any user with a law license requires a paid subscription of CAD $300/month."
                    )
                }
            )
        }
    }
}

private fun pyKey(py: Python, key: String): PyObject = py.getModule("builtins").callAttr("str", key)

private fun pyGet(map: Map<PyObject?, PyObject?>, py: Python, key: String): PyObject? = map[pyKey(py, key)]

private fun pyGetString(map: Map<PyObject?, PyObject?>, py: Python, key: String): String =
    pyGet(map, py, key)?.toString() ?: ""

private fun asMapOrNull(obj: PyObject?): Map<PyObject?, PyObject?>? {
    if (obj == null || obj.toString() == "None") return null
    return try { obj.asMap() } catch (_: Exception) { null }
}

private fun asListOrEmpty(obj: PyObject?): List<PyObject?> {
    if (obj == null || obj.toString() == "None") return emptyList()
    return try { obj.asList() } catch (_: Exception) { emptyList() }
}

private fun asStringPairs(map: Map<PyObject?, PyObject?>?): List<Pair<String, String>> {
    if (map == null) return emptyList()
    return map.entries.mapNotNull { (k, v) ->
        val key = k?.toString()?.trim().orEmpty()
        val value = v?.toString()?.trim().orEmpty()
        if (key.isBlank() || value.isBlank()) null else key to value
    }
}

private fun renderAudioTran(results: PyObject): String {
    val py = Python.getInstance()
    return runCatching {
        py.getModule("json").callAttr("dumps", results).toString() + "\n"
    }.getOrElse {
        results.toString() + "\n"
    }
}

private fun writeAudioTranFile(context: Context, results: PyObject): String {
    val baseDir = context.getExternalFilesDir(null) ?: context.filesDir
    val outFile = File(baseDir, "audiotran")
    outFile.writeText(renderAudioTran(results), Charsets.UTF_8)
    return outFile.absolutePath
}

private fun severityRank(level: String): Int = when (level.uppercase()) {
    "HIGH", "HIGH CONCERN" -> 3
    "MEDIUM", "REVIEW REQUIRED" -> 2
    "LOW" -> 1
    else -> 0
}

private val DisclosureColorScheme = darkColorScheme(
    background = Color(0xFF111111),
    surface = Color(0xFF171717),
    surfaceVariant = Color(0xFF1E1E1E),
    primary = Color(0xFFECECEC),
    secondary = Color(0xFFB8B8B8),
    tertiary = Color(0xFF8F8F8F),
    onBackground = Color(0xFFF2F2F2),
    onSurface = Color(0xFFF2F2F2),
    onSurfaceVariant = Color(0xFFD0D0D0),
    outline = Color(0xFF4A4A4A)
)

@Composable
private fun HeroHeader(modifier: Modifier = Modifier) {
    Card(
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        shape = RoundedCornerShape(20.dp)
    ) {
        Column(Modifier.fillMaxWidth().padding(14.dp)) {
            Image(
                painter = painterResource(id = R.drawable.ic_launcher_logo_foreground),
                contentDescription = "Phoenix logo",
                modifier = Modifier.fillMaxWidth().height(180.dp),
                contentScale = ContentScale.Fit
            )
            Spacer(Modifier.height(10.dp))
            Text("Disclosure Analysis Tool", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Text(
                "Simple report review with direct dictionary-backed output.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
private fun AvResultView(
    resultsMap: Map<PyObject?, PyObject?>,
    py: Python,
    textToAnalyze: String,
    onRescan: (String) -> Unit,
    onBack: () -> Unit
) {
    val transcript = pyGetString(resultsMap, py, "av_transcript_text")
    val mediaErrors = asListOrEmpty(pyGet(resultsMap, py, "media_errors"))
    val comparison = asMapOrNull(pyGet(resultsMap, py, "comparison"))
    val conflict = asMapOrNull(pyGet(resultsMap, py, "evidence_conflict_assessment"))
    val perjury = asMapOrNull(pyGet(resultsMap, py, "perjury_risk_indicators"))
    val stinchcombe = asMapOrNull(pyGet(resultsMap, py, "stinchcombe_conversation_assessment"))
    val runs = asListOrEmpty(pyGet(resultsMap, py, "transcription_runs"))
    val contradictions = asListOrEmpty(comparison?.let { pyGet(it, py, "contradictions") })

    LazyColumn(Modifier.fillMaxSize()) {
        item {
            Row(Modifier.fillMaxWidth(), Arrangement.SpaceBetween, Alignment.CenterVertically) {
                Text("A/V Analysis Results", style = MaterialTheme.typography.titleLarge)
                Row {
                    TextButton(onClick = { onRescan(textToAnalyze) }) { Text("Redo") }
                    TextButton(onClick = onBack) { Text("Back") }
                }
            }
            Divider(Modifier.padding(vertical = 8.dp))
        }

        item {
            Card(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                Column(Modifier.padding(12.dp)) {
                    Text("Evidence Conflict", fontWeight = FontWeight.Bold)
                    Text(conflict?.let { pyGetString(it, py, "summary") }.orEmpty().ifBlank { "No conflict summary generated." },
                        style = MaterialTheme.typography.bodySmall)
                    val conflictCount = conflict?.let { pyGetString(it, py, "conflict_count") }.orEmpty()
                    val consistency = conflict?.let { pyGetString(it, py, "consistency_score") }.orEmpty()
                    if (conflictCount.isNotBlank() || consistency.isNotBlank()) {
                        Text("Conflicts: $conflictCount | Consistency: $consistency", style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }

        if (contradictions.isNotEmpty()) {
            item {
                Card(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                    Column(Modifier.padding(12.dp)) {
                        Text("Contradictions", fontWeight = FontWeight.Bold)
                        contradictions.take(5).forEach { contradictionObj ->
                            val contradiction = asMapOrNull(contradictionObj) ?: return@forEach
                            val witnessSentence = pyGetString(contradiction, py, "witness_sentence")
                            val transcriptSentence = pyGetString(contradiction, py, "transcript_sentence")
                            val certainty = pyGetString(contradiction, py, "certainty")
                            val flags = asListOrEmpty(pyGet(contradiction, py, "conflict_flags"))
                                .mapNotNull { it?.toString() }
                                .filter { it.isNotBlank() }
                                .joinToString(", ")

                            Text("Statement: $witnessSentence", style = MaterialTheme.typography.bodySmall)
                            Text("Transcript: $transcriptSentence", style = MaterialTheme.typography.bodySmall)
                            if (certainty.isNotBlank()) {
                                Text("Certainty: $certainty", style = MaterialTheme.typography.bodySmall)
                            }
                            if (flags.isNotBlank()) {
                                Text("Flags: $flags", style = MaterialTheme.typography.bodySmall)
                            }
                            Spacer(Modifier.height(8.dp))
                        }
                    }
                }
            }
        }

        item {
            Card(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                Column(Modifier.padding(12.dp)) {
                    Text("Perjury Risk Indicators", fontWeight = FontWeight.Bold)
                    val level = perjury?.let { pyGetString(it, py, "risk_level") }.orEmpty()
                    val score = perjury?.let { pyGetString(it, py, "risk_score") }.orEmpty()
                    if (level.isNotBlank()) {
                        Text("Level: $level (score $score)", style = MaterialTheme.typography.bodySmall)
                    }
                    val indicators = asListOrEmpty(perjury?.let { pyGet(it, py, "indicators") })
                    if (indicators.isEmpty()) {
                        Text("No indicators reported.", style = MaterialTheme.typography.bodySmall)
                    } else {
                        indicators.forEach { i ->
                            Text("• ${i?.toString().orEmpty()}", style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
            }
        }

        item {
            Card(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                Column(Modifier.padding(12.dp)) {
                    Text("Stinchcombe Conversation Fit", fontWeight = FontWeight.Bold)
                    val level = stinchcombe?.let { pyGetString(it, py, "level") }.orEmpty()
                    val score = stinchcombe?.let { pyGetString(it, py, "score") }.orEmpty()
                    if (level.isNotBlank()) {
                        Text("Level: $level (score $score)", style = MaterialTheme.typography.bodySmall)
                    }
                    val assessment = stinchcombe?.let { pyGetString(it, py, "assessment") }.orEmpty()
                    if (assessment.isNotBlank()) {
                        Spacer(Modifier.height(6.dp))
                        Text(assessment, style = MaterialTheme.typography.bodySmall)
                    }
                    val findings = asListOrEmpty(stinchcombe?.let { pyGet(it, py, "findings") })
                    if (findings.isNotEmpty()) {
                        Spacer(Modifier.height(6.dp))
                        findings.take(3).forEach { findingObj ->
                            val finding = asMapOrNull(findingObj) ?: return@forEach
                            val label = pyGetString(finding, py, "label")
                            val matches = asListOrEmpty(pyGet(finding, py, "matches"))
                                .mapNotNull { it?.toString() }
                                .filter { it.isNotBlank() }
                                .take(2)
                                .joinToString(" | ")
                            Text("• $label", style = MaterialTheme.typography.bodySmall)
                            if (matches.isNotBlank()) {
                                Text("  $matches", style = MaterialTheme.typography.bodySmall)
                            }
                        }
                    }
                }
            }
        }

        if (runs.isNotEmpty()) {
            item {
                Card(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                    Column(Modifier.padding(12.dp)) {
                        Text("Transcription Runs", fontWeight = FontWeight.Bold)
                        runs.forEach { runObj ->
                            val run = asMapOrNull(runObj)
                            if (run != null) {
                                val source = pyGetString(run, py, "source_type")
                                val engine = pyGetString(run, py, "engine")
                                val words = pyGetString(run, py, "word_count")
                                val quality = pyGetString(run, py, "quality_score")
                                Text("• $source | engine=$engine | words=$words | quality=$quality",
                                    style = MaterialTheme.typography.bodySmall)
                            }
                        }
                    }
                }
            }
        }

        if (mediaErrors.isNotEmpty()) {
            item {
                Card(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                    Column(Modifier.padding(12.dp)) {
                        Text("Media Processing Errors", fontWeight = FontWeight.Bold, color = Color(0xFFB71C1C))
                        mediaErrors.forEach { err ->
                            Text("• ${err?.toString().orEmpty()}", style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
            }
        }

        item {
            Card(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                Column(Modifier.padding(12.dp)) {
                    Text("Transcript", fontWeight = FontWeight.Bold)
                    if (transcript.isBlank()) {
                        Text("No transcript generated. On Android, prerecorded media transcription depends on the device speech service; review Media Processing Errors for the failure reason.",
                            style = MaterialTheme.typography.bodySmall)
                    } else {
                        Text(transcript, style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }

        item {
            val summary = comparison?.let { pyGetString(it, py, "summary") }.orEmpty()
            if (summary.isNotBlank()) {
                Card(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                    Text(summary, Modifier.padding(12.dp), style = MaterialTheme.typography.bodySmall)
                }
            }
        }
    }
}

@Composable
fun ResultView(results: PyObject, textToAnalyze: String, onRescan: (String) -> Unit, onBack: () -> Unit) {
    val resultsMap = results.asMap()
    val py = Python.getInstance()
    val isAvResult = pyGet(resultsMap, py, "comparison") != null || pyGet(resultsMap, py, "av_transcript_text") != null
    if (isAvResult) {
        AvResultView(resultsMap, py, textToAnalyze, onRescan, onBack)
        return
    }
    var selectedTab by remember { mutableStateOf(0) }
    val tabTitles = listOf(
        "Summary",
        "Breaches",
        "State Conduct",
        "Human Rights",
        "Case Law",
        "Participants"
    )

    val overallAssessment = pyGet(resultsMap, py, "overall_assessment")?.toString() ?: "No assessment"
    val potentialBreaches = asListOrEmpty(pyGet(resultsMap, py, "potential_breaches"))
    val officerConduct = asMapOrNull(pyGet(resultsMap, py, "officer_conduct_assessment"))
    val badFaith = asMapOrNull(pyGet(resultsMap, py, "bad_faith_assessment"))
    val policeIndicators = asListOrEmpty(pyGet(resultsMap, py, "police_misconduct_indicators"))
    val humanRights = asMapOrNull(pyGet(resultsMap, py, "human_rights_assessment"))
    val stinchcombe = asMapOrNull(pyGet(resultsMap, py, "stinchcombe_conversation_assessment"))
    val specificFlags = asListOrEmpty(pyGet(resultsMap, py, "specific_flags"))
    val caseLawReferences = asListOrEmpty(pyGet(resultsMap, py, "case_law_references"))
    val partyNarratives = asMapOrNull(pyGet(resultsMap, py, "party_narratives"))
    val parties = asListOrEmpty(partyNarratives?.let { pyGet(it, py, "parties") })
    val versionRouting = asMapOrNull(partyNarratives?.let { pyGet(it, py, "version_routing") })
    val caseCaption = partyNarratives?.let { pyGetString(it, py, "case_caption") } ?: ""

    val sortedBreaches = potentialBreaches.sortedByDescending { breachObj ->
        val b = asMapOrNull(breachObj) ?: return@sortedByDescending 0
        severityRank(pyGetString(b, py, "confidence_level"))
    }
    val sortedIndicators = policeIndicators.sortedByDescending { indicatorObj ->
        val indicator = asMapOrNull(indicatorObj) ?: return@sortedByDescending 0
        severityRank(pyGetString(indicator, py, "severity"))
    }
    val sortedParties = parties.sortedByDescending { partyObj ->
        val party = asMapOrNull(partyObj) ?: return@sortedByDescending 0
        pyGetString(party, py, "statement_count").toIntOrNull() ?: 0
    }

    Card(
        modifier = Modifier.fillMaxSize(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
        shape = RoundedCornerShape(20.dp)
    ) {
        Column(Modifier.fillMaxSize().padding(14.dp)) {
            Row(Modifier.fillMaxWidth(), Arrangement.SpaceBetween, Alignment.CenterVertically) {
                Text("Analysis Results", style = MaterialTheme.typography.titleLarge)
                Row {
                    TextButton(onClick = { onRescan(textToAnalyze) }) { Text("Redo") }
                    TextButton(onClick = onBack) { Text("Back") }
                }
            }
            Divider(Modifier.padding(vertical = 8.dp))

            Row(Modifier.fillMaxSize()) {
                Card(
                    modifier = Modifier.width(152.dp).fillMaxHeight(),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Column(
                        Modifier.fillMaxSize().padding(10.dp).verticalScroll(rememberScrollState()),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        tabTitles.forEachIndexed { index, title ->
                            FilledTonalButton(
                                onClick = { selectedTab = index },
                                modifier = Modifier.fillMaxWidth(),
                                colors = ButtonDefaults.filledTonalButtonColors(
                                    containerColor = if (selectedTab == index) {
                                        MaterialTheme.colorScheme.primary.copy(alpha = 0.18f)
                                    } else {
                                        MaterialTheme.colorScheme.surfaceVariant
                                    }
                                )
                            ) {
                                Text(title)
                            }
                        }
                    }
                }

                Spacer(Modifier.width(12.dp))

                Column(Modifier.weight(1f).fillMaxHeight()) {
                    Text(
                        text = "${selectedTab + 1}/${tabTitles.size}: ${tabTitles[selectedTab]}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(Modifier.height(8.dp))

                    when (selectedTab) {
            0 -> {
                LazyColumn(Modifier.weight(1f)) {
                    item {
                        Card(Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
                            Text(overallAssessment, Modifier.padding(12.dp))
                        }
                    }
                    item {
                        Card(Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
                            Column(Modifier.padding(12.dp)) {
                                Text("Fact-check flow", fontWeight = FontWeight.Bold)
                                Text("1. Review top Charter breach cards by confidence.", style = MaterialTheme.typography.bodySmall)
                                Text("2. Open State Conduct for duty-to-consider-evidence findings.", style = MaterialTheme.typography.bodySmall)
                                Text("3. Open Human Rights tab for UN/Canada/Ontario layered flags.", style = MaterialTheme.typography.bodySmall)
                                Text("4. Cross-check missing evidence claims against the source document text.", style = MaterialTheme.typography.bodySmall)
                                Text("5. Open Case Law tab for direct case links and section-specific sources.", style = MaterialTheme.typography.bodySmall)
                            }
                        }
                    }
                    item {
                        Card(Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
                            Column(Modifier.padding(12.dp)) {
                                val hrLevel = humanRights?.let { pyGetString(it, py, "level") }.orEmpty()
                                val hrScore = humanRights?.let { pyGetString(it, py, "score") }.orEmpty()
                                if (hrLevel.isNotBlank()) {
                                    Text("Human Rights Risk: $hrLevel", fontWeight = FontWeight.Bold)
                                    if (hrScore.isNotBlank()) {
                                        Text("Human Rights Score: $hrScore", style = MaterialTheme.typography.bodySmall)
                                    }
                                }
                                if (specificFlags.isNotEmpty()) {
                                    Text("Human Rights Flags: ${specificFlags.size}", style = MaterialTheme.typography.bodySmall)
                                }
                            }
                        }
                    }
                    item {
                        Card(Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
                            Column(Modifier.padding(12.dp)) {
                                val sLevel = stinchcombe?.let { pyGetString(it, py, "level") }.orEmpty()
                                val sScore = stinchcombe?.let { pyGetString(it, py, "score") }.orEmpty()
                                if (sLevel.isNotBlank()) {
                                    Text("Stinchcombe Fit: $sLevel", fontWeight = FontWeight.Bold)
                                    if (sScore.isNotBlank()) {
                                        Text("Stinchcombe Score: $sScore", style = MaterialTheme.typography.bodySmall)
                                    }
                                }
                                val sAssessment = stinchcombe?.let { pyGetString(it, py, "assessment") }.orEmpty()
                                if (sAssessment.isNotBlank()) {
                                    Spacer(Modifier.height(6.dp))
                                    Text(sAssessment, style = MaterialTheme.typography.bodySmall)
                                }
                            }
                        }
                    }
                }
            }
            1 -> {
                LazyColumn(Modifier.weight(1f)) {
                    items(sortedBreaches) { breachObj ->
                        val b = asMapOrNull(breachObj)
                        if (b != null) {
                            val section = pyGetString(b, py, "section")
                            val title = pyGetString(b, py, "title").ifBlank { "Breach" }
                            val description = pyGetString(b, py, "description")
                            val confidence = pyGetString(b, py, "confidence_level")

                            Card(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                                Column(Modifier.padding(12.dp)) {
                                    Text("Section $section", fontWeight = FontWeight.Bold)
                                    Text(title, style = MaterialTheme.typography.titleSmall)
                                    if (confidence.isNotBlank()) {
                                        Text("Confidence: $confidence", style = MaterialTheme.typography.bodySmall)
                                    }
                                    Text(description, style = MaterialTheme.typography.bodySmall)
                                }
                            }
                        }
                    }
                }
            }
            2 -> {
                LazyColumn(Modifier.weight(1f)) {
                    item {
                        Card(Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
                            Column(Modifier.padding(12.dp)) {
                                Text("State Conduct Assessment", fontWeight = FontWeight.Bold)
                                if (officerConduct == null && badFaith == null) {
                                    Text("No state-conduct assessment was generated for this record.")
                                } else {
                                    officerConduct?.let { oc ->
                                        val seriousness = pyGetString(oc, py, "seriousness")
                                        val legalBasis = pyGetString(oc, py, "legal_basis")
                                        val assessment = pyGetString(oc, py, "assessment")
                                        Text("Seriousness: $seriousness", style = MaterialTheme.typography.bodySmall)
                                        Text("Legal Basis: $legalBasis", style = MaterialTheme.typography.bodySmall)
                                        Spacer(Modifier.height(8.dp))
                                        Text(assessment, style = MaterialTheme.typography.bodySmall)
                                        val findings = asListOrEmpty(pyGet(oc, py, "findings"))
                                        if (findings.isNotEmpty()) {
                                            Spacer(Modifier.height(8.dp))
                                            Text("Findings", fontWeight = FontWeight.Bold)
                                            findings.forEach { finding ->
                                                Text("• ${finding?.toString().orEmpty()}", style = MaterialTheme.typography.bodySmall)
                                            }
                                        }
                                    }

                                    badFaith?.let { bf ->
                                        Spacer(Modifier.height(10.dp))
                                        Text("Official Bad Faith", fontWeight = FontWeight.Bold)
                                        Text("Level: ${pyGetString(bf, py, "level")} (score ${pyGetString(bf, py, "score")})",
                                            style = MaterialTheme.typography.bodySmall)
                                        Text("Legal Basis: ${pyGetString(bf, py, "legal_basis")}", style = MaterialTheme.typography.bodySmall)
                                        Spacer(Modifier.height(6.dp))
                                        Text(pyGetString(bf, py, "assessment"), style = MaterialTheme.typography.bodySmall)
                                    }
                                }
                            }
                        }
                    }

                    if (sortedIndicators.isNotEmpty()) {
                        item {
                            Text("Indicators (ordered by relevance)", fontWeight = FontWeight.Bold, modifier = Modifier.padding(top = 4.dp))
                        }
                        items(sortedIndicators) { indicatorObj ->
                            val indicator = asMapOrNull(indicatorObj)
                            if (indicator != null) {
                                val name = pyGetString(indicator, py, "indicator")
                                val severity = pyGetString(indicator, py, "severity")
                                val summary = pyGetString(indicator, py, "summary")
                                val source = pyGetString(indicator, py, "source")
                                val url = pyGetString(indicator, py, "url")
                                Card(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                                    Column(Modifier.padding(12.dp)) {
                                        Text(name.ifBlank { "Indicator" }, fontWeight = FontWeight.Bold)
                                        Text("Severity: $severity", style = MaterialTheme.typography.bodySmall)
                                        Text("Source: $source", style = MaterialTheme.typography.bodySmall)
                                        if (summary.isNotBlank()) Text(summary, style = MaterialTheme.typography.bodySmall)
                                        if (url.isNotBlank()) Text(url, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.tertiary)
                                    }
                                }
                            }
                        }
                    }
                }
            }
            3 -> {
                LazyColumn(Modifier.weight(1f)) {
                    item {
                        Card(Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
                            Column(Modifier.padding(12.dp)) {
                                Text("Human Rights Assessment", fontWeight = FontWeight.Bold)
                                if (humanRights == null) {
                                    Text("No human-rights assessment was generated for this record.")
                                } else {
                                    val level = pyGetString(humanRights, py, "level")
                                    val score = pyGetString(humanRights, py, "score")
                                    val assessment = pyGetString(humanRights, py, "assessment")
                                    Text("Level: $level (score $score)", style = MaterialTheme.typography.bodySmall)
                                    Spacer(Modifier.height(6.dp))
                                    Text(assessment, style = MaterialTheme.typography.bodySmall)

                                    val grounds = asListOrEmpty(pyGet(humanRights, py, "protected_grounds"))
                                        .mapNotNull { it?.toString() }
                                        .filter { it.isNotBlank() }
                                    if (grounds.isNotEmpty()) {
                                        Spacer(Modifier.height(8.dp))
                                        Text("Protected grounds detected: ${grounds.joinToString(", ")}", style = MaterialTheme.typography.bodySmall)
                                    }
                                }
                            }
                        }
                    }

                    if (specificFlags.isNotEmpty()) {
                        item {
                            Text("Flagged signals", fontWeight = FontWeight.Bold, modifier = Modifier.padding(top = 4.dp))
                        }
                        items(specificFlags) { flagObj ->
                            val flag = asMapOrNull(flagObj)
                            if (flag != null) {
                                val label = pyGetString(flag, py, "label")
                                val description = pyGetString(flag, py, "description")
                                val count = pyGetString(flag, py, "count")
                                Card(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                                    Column(Modifier.padding(12.dp)) {
                                        Text(label.ifBlank { "Flag" }, fontWeight = FontWeight.Bold)
                                        if (count.isNotBlank()) {
                                            Text("Matches: $count", style = MaterialTheme.typography.bodySmall)
                                        }
                                        if (description.isNotBlank()) {
                                            Text(description, style = MaterialTheme.typography.bodySmall)
                                        }
                                    }
                                }
                            }
                        }
                    }

                    val findings = asListOrEmpty(humanRights?.let { pyGet(it, py, "findings") })
                    if (findings.isNotEmpty()) {
                        item {
                            Text("Framework findings", fontWeight = FontWeight.Bold, modifier = Modifier.padding(top = 4.dp))
                        }
                        items(findings) { findingObj ->
                            val finding = asMapOrNull(findingObj)
                            if (finding != null) {
                                val criterion = pyGetString(finding, py, "criterion")
                                val summary = pyGetString(finding, py, "summary")
                                val layers = asListOrEmpty(pyGet(finding, py, "layers"))
                                    .mapNotNull { it?.toString() }
                                    .filter { it.isNotBlank() }
                                    .joinToString(" | ")
                                val cases = asListOrEmpty(pyGet(finding, py, "cases"))
                                    .mapNotNull { caseObj ->
                                        val caseMap = asMapOrNull(caseObj) ?: return@mapNotNull null
                                        val title = pyGetString(caseMap, py, "title")
                                        val citation = pyGetString(caseMap, py, "citation")
                                        if (title.isBlank() && citation.isBlank()) null
                                        else listOf(title, citation).filter { it.isNotBlank() }.joinToString(" — ")
                                    }
                                    .filter { it.isNotBlank() }
                                    .joinToString(" | ")

                                Card(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                                    Column(Modifier.padding(12.dp)) {
                                        Text(criterion.ifBlank { "Human-rights criterion" }, fontWeight = FontWeight.Bold)
                                        if (summary.isNotBlank()) {
                                            Text(summary, style = MaterialTheme.typography.bodySmall)
                                        }
                                        if (layers.isNotBlank()) {
                                            Spacer(Modifier.height(6.dp))
                                            Text("Layers: $layers", style = MaterialTheme.typography.bodySmall)
                                        }
                                        if (cases.isNotBlank()) {
                                            Spacer(Modifier.height(6.dp))
                                            Text("Cases: $cases", style = MaterialTheme.typography.bodySmall)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            4 -> {
                LazyColumn(Modifier.weight(1f)) {
                    if (caseLawReferences.isEmpty()) {
                        item {
                            Text(
                                "No structured case-law references were generated for this record.",
                                style = MaterialTheme.typography.bodySmall
                            )
                        }
                    } else {
                        items(caseLawReferences) { refObj ->
                            val ref = asMapOrNull(refObj)
                            if (ref != null) {
                                val section = pyGetString(ref, py, "section")
                                val title = pyGetString(ref, py, "title")
                                val governingTest = pyGetString(ref, py, "governing_test")
                                val conclusion = pyGetString(ref, py, "conclusion")
                                val clnReference = pyGetString(ref, py, "cln_reference")
                                val authorityLinks = asListOrEmpty(pyGet(ref, py, "authority_links"))
                                val topResultLinks = asListOrEmpty(pyGet(ref, py, "top_result_links"))
                                val searchUrlPairs = asStringPairs(asMapOrNull(pyGet(ref, py, "canlii_search_urls")))

                                Card(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                                    Column(Modifier.padding(12.dp)) {
                                        Text("Section $section ${if (title.isNotBlank()) "— $title" else ""}".trim(), fontWeight = FontWeight.Bold)
                                        if (governingTest.isNotBlank()) {
                                            Spacer(Modifier.height(6.dp))
                                            Text("Test: $governingTest", style = MaterialTheme.typography.bodySmall)
                                        }
                                        if (conclusion.isNotBlank()) {
                                            Spacer(Modifier.height(6.dp))
                                            Text("Finding: $conclusion", style = MaterialTheme.typography.bodySmall)
                                        }

                                        if (authorityLinks.isNotEmpty()) {
                                            Spacer(Modifier.height(8.dp))
                                            Text("Leading authorities", fontWeight = FontWeight.Bold, style = MaterialTheme.typography.bodySmall)
                                            authorityLinks.forEach { linkObj ->
                                                val link = asMapOrNull(linkObj) ?: return@forEach
                                                val citation = pyGetString(link, py, "citation")
                                                val url = pyGetString(link, py, "url")
                                                val locationType = pyGetString(link, py, "location_type")
                                                val pinpoint = pyGetString(link, py, "pinpoint")
                                                val locationLabel = when (locationType) {
                                                    "direct_decision" -> "Direct decision URL"
                                                    "api_result" -> "Case result URL"
                                                    else -> "Search URL"
                                                }
                                                Text("• $citation", style = MaterialTheme.typography.bodySmall)
                                                if (pinpoint.isNotBlank()) {
                                                    Text("  Pinpoint: $pinpoint", style = MaterialTheme.typography.bodySmall)
                                                }
                                                Text("  $locationLabel: $url", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.tertiary)
                                            }
                                        }

                                        if (topResultLinks.isNotEmpty()) {
                                            Spacer(Modifier.height(8.dp))
                                            Text("Top CanLII results", fontWeight = FontWeight.Bold, style = MaterialTheme.typography.bodySmall)
                                            topResultLinks.forEach { linkObj ->
                                                val link = asMapOrNull(linkObj) ?: return@forEach
                                                val citation = pyGetString(link, py, "citation")
                                                val url = pyGetString(link, py, "url")
                                                if (citation.isNotBlank()) Text("• $citation", style = MaterialTheme.typography.bodySmall)
                                                if (url.isNotBlank()) Text("  $url", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.tertiary)
                                            }
                                        }

                                        if (searchUrlPairs.isNotEmpty()) {
                                            Spacer(Modifier.height(8.dp))
                                            Text("CanLII search links", fontWeight = FontWeight.Bold, style = MaterialTheme.typography.bodySmall)
                                            searchUrlPairs.forEach { (name, url) ->
                                                Text("• $name: $url", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.tertiary)
                                            }
                                        }

                                        if (clnReference.isNotBlank()) {
                                            Spacer(Modifier.height(8.dp))
                                            Text("Criminal Law Notebook: $clnReference", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.tertiary)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            else -> {
                LazyColumn(Modifier.weight(1f)) {
                    item {
                        Card(Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
                            Column(Modifier.padding(12.dp)) {
                                Text("Participant and Narrative Extraction", fontWeight = FontWeight.Bold)
                                if (caseCaption.isNotBlank()) {
                                    Text("Case caption: $caseCaption", style = MaterialTheme.typography.bodySmall)
                                }
                                if (versionRouting != null) {
                                    Text(
                                        "Suggested version: ${pyGetString(versionRouting, py, "recommended_version")}",
                                        style = MaterialTheme.typography.bodySmall
                                    )
                                    Text(
                                        pyGetString(versionRouting, py, "reason"),
                                        style = MaterialTheme.typography.bodySmall
                                    )
                                }
                            }
                        }
                    }

                    if (sortedParties.isEmpty()) {
                        item {
                            Text(
                                "No clearly identifiable names/roles were extracted from this text.",
                                style = MaterialTheme.typography.bodySmall
                            )
                        }
                    } else {
                        items(sortedParties) { partyObj ->
                            val party = asMapOrNull(partyObj)
                            if (party != null) {
                                val name = pyGetString(party, py, "name")
                                val role = pyGetString(party, py, "primary_role")
                                val rolesList = asListOrEmpty(pyGet(party, py, "roles"))
                                    .joinToString(", ") { it?.toString().orEmpty() }
                                val statements = asListOrEmpty(pyGet(party, py, "what_they_say_happened"))
                                val contextTags = asListOrEmpty(pyGet(party, py, "context_tags"))
                                    .map { it?.toString().orEmpty() }
                                    .filter { it.isNotBlank() }
                                    .joinToString(", ")

                                Card(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                                    Column(Modifier.padding(12.dp)) {
                                        Text(name.ifBlank { "Unnamed Participant" }, fontWeight = FontWeight.Bold)
                                        Text("Primary role: $role", style = MaterialTheme.typography.bodySmall)
                                        if (rolesList.isNotBlank()) {
                                            Text("All roles: $rolesList", style = MaterialTheme.typography.bodySmall)
                                        }
                                        if (contextTags.isNotBlank()) {
                                            Text("Context: $contextTags", style = MaterialTheme.typography.bodySmall)
                                        }
                                        Spacer(Modifier.height(6.dp))
                                        Text("Captured excerpts:", fontWeight = FontWeight.Bold, style = MaterialTheme.typography.bodySmall)
                                        if (statements.isEmpty()) {
                                            Text("No direct statement verb was detected for this participant.", style = MaterialTheme.typography.bodySmall)
                                        } else {
                                            statements.forEach { s ->
                                                Text("• ${s?.toString().orEmpty()}", style = MaterialTheme.typography.bodySmall)
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
            }
        }
    }
}
