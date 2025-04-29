#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QTextEdit>
#include <QLineEdit>
#include <QPushButton>
#include <QProcess>

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void onSendClicked();
    void onOllamaFinished(int exitCode, QProcess::ExitStatus exitStatus);

private:
    QTextEdit *chatDisplay;
    QLineEdit *inputLine;
    QPushButton *sendButton;
    QProcess *ollamaProcess;

    void appendMessage(const QString &sender, const QString &message);
};

#endif // MAINWINDOW_H
