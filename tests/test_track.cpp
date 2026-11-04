#include <QtTest>
#include <QTemporaryFile>
#include <QTemporaryDir>
#include <QDir>
#include <QProcess>
#include "track.h"
#include "file_utils.h"
#include "csv_import.h"
#include "itunes_sync.h"

#include "test_track.h"

void TestTrack::initTestCase()
{
    QVERIFY(m_tempDir.isValid());
    
    // Create a temporary MP3 file for testing
    QTemporaryFile tempFile;
    tempFile.setFileTemplate(m_tempDir.path() + "/test_track_XXXXXX.mp3");
    if (tempFile.open()) {
        m_testFilePath = tempFile.fileName();
        tempFile.close();
    }
}

void TestTrack::cleanupTestCase()
{
    // Temporary files are cleaned up automatically
}

void TestTrack::testLoadNonexistentFile()
{
    metatag::Track track("/nonexistent/file.mp3");
    QVERIFY(!track.load());
    QVERIFY(!track.isLoaded());
}

void TestTrack::testLoadInvalidFile()
{
    // Create an empty file (not a valid audio file)
    QFile file(m_testFilePath);
    QVERIFY(file.open(QIODevice::WriteOnly));
    file.write("not an audio file");
    file.close();

    metatag::Track track(m_testFilePath);
    QVERIFY(!track.load());
    QVERIFY(!track.isLoaded());
}

void TestTrack::testCreateAndLoadTrack()
{
    metatag::Track track(m_testFilePath);
    QCOMPARE(track.filePath(), m_testFilePath);
    QVERIFY(!track.isLoaded());
    QVERIFY(!track.isDirty());
}

void TestTrack::testSetProperties()
{
    metatag::Track track(m_testFilePath);
    track.setArtist("Test Artist");
    track.setAlbum("Test Album");
    track.setTitle("Test Title");
    track.setTrackNumber(1);
    track.setGenre("Test Genre");
    track.setYear(2023);

    QCOMPARE(track.artist(), QString("Test Artist"));
    QCOMPARE(track.album(), QString("Test Album"));
    QCOMPARE(track.title(), QString("Test Title"));
    QCOMPARE(track.trackNumber(), 1);
    QCOMPARE(track.genre(), QString("Test Genre"));
    QCOMPARE(track.year(), 2023);
    QVERIFY(track.isDirty());
}

void TestTrack::testSaveTrack()
{
    // This test assumes we have a valid audio file
    // For now, just test that save returns false for invalid file
    metatag::Track track(m_testFilePath);
    QVERIFY(!track.save()); // Should fail for invalid file
}

void TestTrack::testFileUtils()
{
    // Test safeDelete on non-existent file
    QVERIFY(metatag::FileUtils::safeDelete("/nonexistent/file.txt"));
    
    // Test with temporary files
    QString tempPath = m_tempDir.path() + "/test_file.txt";
    {
        QFile tempFile(tempPath);
        QVERIFY(tempFile.open(QIODevice::WriteOnly));
        tempFile.write("test");
        tempFile.close();
    }
    
    QVERIFY(QFile::exists(tempPath));

    // Test safeMove and safeCopy on the same file (Finding #8)
    QVERIFY(metatag::FileUtils::safeMove(tempPath, tempPath));
    QVERIFY(QFile::exists(tempPath));
    QVERIFY(metatag::FileUtils::safeCopy(tempPath, tempPath));
    QVERIFY(QFile::exists(tempPath));

    // Test safeCopy to new path
    QString copyPath = m_tempDir.path() + "/copied.txt";
    QVERIFY(metatag::FileUtils::safeCopy(tempPath, copyPath));
    QVERIFY(QFile::exists(copyPath));
    QVERIFY(QFile::exists(tempPath));

    QVERIFY(metatag::FileUtils::safeDelete(copyPath));
    QVERIFY(metatag::FileUtils::safeDelete(tempPath));
    QVERIFY(!QFile::exists(tempPath));
}

void TestTrack::testFindAudioFiles()
{
    // Create some test files
    QString mp3Path = m_tempDir.path() + "/test.mp3";
    QString txtPath = m_tempDir.path() + "/test.txt";
    QString flacPath = m_tempDir.path() + "/test.flac";
    
    QFile mp3File(mp3Path);
    QVERIFY(mp3File.open(QIODevice::WriteOnly));
    mp3File.close();
    
    QFile txtFile(txtPath);
    QVERIFY(txtFile.open(QIODevice::WriteOnly));
    txtFile.close();
    
    QFile flacFile(flacPath);
    QVERIFY(flacFile.open(QIODevice::WriteOnly));
    flacFile.close();
    
    QDir dir(m_tempDir.path());
    dir.mkdir("cycle_dir");
    QFile::link(m_tempDir.path(), m_tempDir.path() + "/cycle_dir/loop_link");

    auto audioFiles = metatag::FileUtils::findAudioFiles(m_tempDir.path());
    QVERIFY(audioFiles.contains(mp3Path));
    QVERIFY(audioFiles.contains(flacPath));
    QVERIFY(!audioFiles.contains(txtPath));
}

void TestTrack::testNativeCsvMultilineParsing()
{
    QString csvPath = m_tempDir.path() + "/multiline_test.csv";
    QFile file(csvPath);
    QVERIFY(file.open(QIODevice::WriteOnly | QIODevice::Text));
    QTextStream out(&file);
    out << "File,Artist,Title,Comment\n";
    out << "\"" << m_testFilePath << "\",\"Queen\",\"Bohemian Rhapsody\",\"Line 1\nLine 2 with \"\"quotes\"\"\"\n";
    file.close();

    QVector<metatag::Track> tracks;
    metatag::CsvImport importer;
    bool ok = importer.import(csvPath, tracks);
    QVERIFY(ok);
}

void TestTrack::testNativeItunesFormattedXml()
{
    QString xmlPath = m_tempDir.path() + "/itunes_formatted.xml";
    QFile file(xmlPath);
    QVERIFY(file.open(QIODevice::WriteOnly | QIODevice::Text));
    QTextStream out(&file);
    out << "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        << "<!DOCTYPE plist PUBLIC \"-//Apple Computer//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n"
        << "<plist version=\"1.0\">\n"
        << "<dict>\n"
        << "    <key>Major Version</key><integer>1</integer>\n"
        << "    <key>Tracks</key>\n"
        << "    <dict>\n"
        << "        <key>100</key>\n"
        << "        <dict>\n"
        << "            <key>Track ID</key><integer>100</integer>\n"
        << "            <key>Name</key><string>Test Title</string>\n"
        << "            <key>Artist</key><string>Test Artist</string>\n"
        << "            <key>Track Number</key><integer>3</integer>\n"
        << "            <key>Year</key><integer>2024</integer>\n"
        << "            <key>Location</key><string>file:///tmp/song.mp3</string>\n"
        << "        </dict>\n"
        << "    </dict>\n"
        << "</dict>\n"
        << "</plist>\n";
    file.close();

    QVector<metatag::Track> tracks;
    metatag::iTunesSync itunes;
    bool ok = itunes.importLibrary(xmlPath, tracks);
    QVERIFY(ok);
}

void TestTrack::testRealAudioRoundtrip()
{
    QString realMp3 = m_tempDir.path() + "/real_test.mp3";
    QStringList args;
    args << "-y" << "-loglevel" << "error"
         << "-f" << "lavfi" << "-i" << "sine=frequency=440:duration=0.1"
         << "-c:a" << "libmp3lame" << realMp3;
    int exitCode = QProcess::execute("ffmpeg", args);
    if (exitCode != 0) {
        QSKIP("ffmpeg is not available or failed to generate test audio");
    }

    metatag::Track track(realMp3);
    QVERIFY(track.load());
    QVERIFY(track.isLoaded());

    track.setArtist("Native Artist");
    track.setAlbum("Native Album");
    track.setTitle("Native Title");
    track.setGenre("Native Genre");
    track.setYear(2025);
    track.setTrackNumber(7);
    track.setComment("Native Comment");

    QVERIFY(track.isDirty());
    QVERIFY(track.save());
    QVERIFY(!track.isDirty());

    // Reload into a separate instance
    metatag::Track reloaded(realMp3);
    QVERIFY(reloaded.load());
    QCOMPARE(reloaded.artist(), QString("Native Artist"));
    QCOMPARE(reloaded.album(), QString("Native Album"));
    QCOMPARE(reloaded.title(), QString("Native Title"));
    QCOMPARE(reloaded.genre(), QString("Native Genre"));
    QCOMPARE(reloaded.year(), 2025);
    QCOMPARE(reloaded.trackNumber(), 7);
    QCOMPARE(reloaded.comment(), QString("Native Comment"));
}