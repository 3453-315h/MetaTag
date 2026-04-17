#include <QtTest>

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    app.setAttribute(Qt::AA_Use96Dpi, true);

    int status = 0;
    auto runTest = [&status](QObject* test) {
        status |= QTest::qExec(test, QCoreApplication::arguments());
    };

    // Add test objects here as they are created
    runTest(new TestTrack);

    return status;
}