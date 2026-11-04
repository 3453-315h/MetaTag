#include <QCoreApplication>
#include <QtTest>
#include "test_track.h"

int main(int argc, char *argv[])
{
    QCoreApplication app(argc, argv);

    int status = 0;
    auto runTest = [&status](QObject* test) {
        status |= QTest::qExec(test, QCoreApplication::arguments());
    };

    // Add test objects here as they are created
    runTest(new TestTrack);

    return status;
}