#include <QtTest>
#include <QTemporaryFile>
#include <QTemporaryDir>
#include <QDir>
#include "track.h"
#include "file_utils.h"

class TestTrack : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void cleanupTestCase();
    void testLoadNonexistentFile();
    void testLoadInvalidFile();
    void testCreateAndLoadTrack();
    void testSetProperties();
    void testSaveTrack();
    void testFileUtils();
    void testFindAudioFiles();

private:
    QString m_testFilePath;
    QTemporaryDir m_tempDir;
};

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
    QTemporaryFile tempFile(m_tempDir.path() + "/test_XXXXXX.txt");
    QVERIFY(tempFile.open());
    QString tempPath = tempFile.fileName();
    tempFile.write("test");
    tempFile.close();
    
    QVERIFY(QFile::exists(tempPath));
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
    mp3File.open(QIODevice::WriteOnly);
    mp3File.close();
    
    QFile txtFile(txtPath);
    txtFile.open(QIODevice::WriteOnly);
    txtFile.close();
    
    QFile flacFile(flacPath);
    flacFile.open(QIODevice::WriteOnly);
    flacFile.close();
    
    auto audioFiles = metatag::FileUtils::findAudioFiles(m_tempDir.path());
    QVERIFY(audioFiles.contains(mp3Path));
    QVERIFY(audioFiles.contains(flacPath));
    QVERIFY(!audioFiles.contains(txtPath));
}

QTEST_MAIN(TestTrack)
#include "test_track.moc"