fun triggerPanicWipe(context: Context) {
    // 1. Clear SharedPreferences/Encrypted Files
    val sharedPrefs = context.getSharedPreferences("secure_prefs", Context.MODE_PRIVATE)
    sharedPrefs.edit().clear().apply()

    // 2. Clear Database (assuming Room)
    // AppDatabase.getInstance(context).clearAllTables()

    // 3. Clear Cache & Files
    context.cacheDir.deleteRecursively()
    context.filesDir.deleteRecursively()

    // 4. Force Close App to a "Safe" screen (e.g., a simple Calculator or News feed)
    val intent = Intent(context, SafeDecoyActivity::class.java)
    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
    context.startActivity(intent)
}