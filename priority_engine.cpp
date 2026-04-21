#include <iostream>
#include <string>
#include <memory>
#include <vector>
#include <algorithm>
#include <ctime>

struct Incident {
    std::string id;
    int severity;
    long long timestamp;
    double priority_score;
};

struct Node {
    Incident data;
    std::unique_ptr<Node> next;
    Node(Incident d) : data(d), next(nullptr) {}
};

double calculateScore(int severity, long long timestamp) {
    long long current_time = std::time(nullptr);
    double seconds_since = std::max(0.0, (double)(current_time - timestamp));
    return (severity * 2.0) + (seconds_since / 60.0);
}

std::unique_ptr<Node> merge(std::unique_ptr<Node> a, std::unique_ptr<Node> b) {
    if (!a) return b;
    if (!b) return a;
    if (a->data.priority_score >= b->data.priority_score) {
        a->next = merge(std::move(a->next), std::move(b));
        return a;
    } else {
        b->next = merge(std::move(a), std::move(b->next));
        return b;
    }
}

std::unique_ptr<Node> split(std::unique_ptr<Node>& head) {
    if (!head || !head->next) return nullptr;
    Node* slow = head.get();
    Node* fast = head.get();
    while (fast->next && fast->next->next) {
        slow = slow->next.get();
        fast = fast->next->next.get();
    }
    std::unique_ptr<Node> second = std::move(slow->next);
    slow->next = nullptr;
    return second;
}

std::unique_ptr<Node> mergeSort(std::unique_ptr<Node> head) {
    if (!head || !head->next) return head;
    std::unique_ptr<Node> second = split(head);
    return merge(mergeSort(std::move(head)), mergeSort(std::move(second)));
}

std::string getVal(const std::string& json, const std::string& key) {
    size_t kpos = json.find("\"" + key + "\"");
    if (kpos == std::string::npos) return "";
    size_t vstart = json.find(":", kpos);
    if (vstart == std::string::npos) return "";
    vstart++;
    while (vstart < json.length() && (json[vstart] == ' ' || json[vstart] == '\"' || json[vstart] == '{' || json[vstart] == '[')) vstart++;
    size_t vend = vstart;
    while (vend < json.length() && json[vend] != '\"' && json[vend] != ',' && json[vend] != '}' && json[vend] != ']') vend++;
    return json.substr(vstart, vend - vstart);
}

int main() {
    std::string input;
    std::string line;
    while (std::getline(std::cin, line)) input += line;
    if (input.empty()) { std::cout << "{\"sorted_ids\": []}" << std::endl; return 0; }

    std::unique_ptr<Node> head = nullptr;

    auto parseAndAdd = [&](const std::string& obj) {
        Incident inc;
        inc.id = getVal(obj, "id");
        if (inc.id.empty()) return;
        try {
            inc.severity = std::stoi(getVal(obj, "severity"));
            inc.timestamp = std::stoll(getVal(obj, "time"));
            inc.priority_score = calculateScore(inc.severity, inc.timestamp);
            auto newNode = std::make_unique<Node>(inc);
            newNode->next = std::move(head);
            head = std::move(newNode);
        } catch (...) {}
    };

    auto findMatchingBrace = [](const std::string& s, size_t openPos) -> size_t {
        int depth = 0;
        for (size_t i = openPos; i < s.length(); i++) {
            if (s[i] == '{') depth++;
            else if (s[i] == '}') { depth--; if (depth == 0) return i; }
        }
        return std::string::npos;
    };

    size_t new_pos = input.find("\"new\"");
    if (new_pos != std::string::npos) {
        size_t start = input.find("{", new_pos);
        size_t end = findMatchingBrace(input, start);
        if (start != std::string::npos && end != std::string::npos) {
            parseAndAdd(input.substr(start, end - start + 1));
        }
    }

    size_t inc_pos = input.find("\"incidents\"");
    if (inc_pos != std::string::npos) {
        size_t arr_start = input.find("[", inc_pos);
        size_t arr_end = input.find("]", arr_start);
        if (arr_start != std::string::npos && arr_end != std::string::npos) {
            std::string arr = input.substr(arr_start, arr_end - arr_start + 1);
            size_t obj_start = arr.find("{");
            while (obj_start != std::string::npos) {
                size_t obj_end = findMatchingBrace(arr, obj_start);
                if (obj_end == std::string::npos) break;
                parseAndAdd(arr.substr(obj_start, obj_end - obj_start + 1));
                obj_start = arr.find("{", obj_end + 1);
            }
        }
    }

    head = mergeSort(std::move(head));

    std::cout << "{\"sorted_ids\": [";
    Node* curr = head.get();
    int count = 0;
    while (curr) {
        if (count > 0) std::cout << ", ";
        std::cout << "\"" << curr->data.id << "\"";
        curr = curr->next.get();
        count++;
    }
    std::cout << "]}" << std::endl;

    return 0;
}


