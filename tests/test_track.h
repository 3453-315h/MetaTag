#ifndef TEST_TRACK_H
#define TEST_TRACK_H

#include <QObject>
#include <QString>
#include <QTemporaryDir>

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
    void testNativeCsvMultilineParsing();
    void testNativeItunesFormattedXml();
    void testRealAudioRoundtrip();

private:
    QString m_testFilePath;
    QTemporaryDir m_tempDir;
};

#endif // TEST_TRACK_H
