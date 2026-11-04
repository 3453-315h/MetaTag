#include <QCoreApplication>
#include <QtTest>
#include <QFile>
#include <cstdio>
#if defined(_WIN32)
#include <windows.h>
#endif
#include "test_track.h"

int main(int argc, char *argv[])
{
#if defined(_WIN32)
    AttachConsole(ATTACH_PARENT_PROCESS);
    freopen("CONOUT$", "w", stdout);
    freopen("CONOUT$", "w", stderr);
#endif

    QCoreApplication app(argc, argv);

    QStringList args;
    for (int i = 0; i < argc; ++i) {
        args << QString::fromLocal8Bit(argv[i]);
    }
    // Also log to test_results.txt
    args << "-o" << "test_results.txt,txt" << "-o" << "-,txt";

    int status = 0;
    auto runTest = [&status, &args](QObject* test) {
        status |= QTest::qExec(test, args);
    };

    // Add test objects here as they are created
    runTest(new TestTrack);

    fflush(stdout);
    fflush(stderr);

    return status;
}