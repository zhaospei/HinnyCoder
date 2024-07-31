package com.plexpt.chatgpt;

import com.plexpt.chatgpt.entity.chat.Message;
import com.plexpt.chatgpt.listener.ConsoleStreamListener;
import com.plexpt.chatgpt.util.Proxys;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.math.BigDecimal;
import java.net.Proxy;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.stream.Collectors;

import cn.hutool.core.util.NumberUtil;
import lombok.SneakyThrows;
import lombok.extern.slf4j.Slf4j;


/**
 * open ai 客户端
 *
 * @author plexpt
 */

@Slf4j

public class ConsoleChatGPT {

    public static Proxy proxy = Proxy.NO_PROXY;

    public static void main(String[] args) {
        String key = getInput("请输入KEY:");
        check(key);

        BigDecimal balance = getBalance(key);
        System.out.println("当前余额: " + balance);

        ChatGPT chatGPT = ChatGPT.builder()
                .apiKey(key)
                .proxy(proxy)
                .build()
                .init();

        while (true) {
            String input = getInput("请输入问题:");
            if (input.equals("exit")) {
                break;
            }
            String answer = chatGPT.chat(input);
            System.out.println("回答: " + answer);
        }
}

    private static BigDecimal getBalance(String key) {

        ChatGPT chatGPT = ChatGPT.builder()
                .apiKey(key)
                .proxy(proxy)
                .build()
                .init();

        return chatGPT.balance();
    }

    private static void check(String key) {
        if (key == null || key.isEmpty()) {
            throw new RuntimeException("请输入正确的KEY");
        }
    }

    @SneakyThrows
    public static String getInput(String prompt) {
        System.out.print(prompt);
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        List<String> lines = new ArrayList<>();
        String line;
        try {
            while ((line = reader.readLine()) != null && !line.isEmpty()) {
                lines.add(line);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return lines.stream().collect(Collectors.joining("\n"));
    }

}

